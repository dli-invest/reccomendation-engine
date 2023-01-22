// moved see https://github.com/dli-invest/dli-fauna-gql/blob/main/fauna.ts
import {
  json,
  serve,
  validateRequest,
} from "https://deno.land/x/sift@0.5.0/mod.ts";

serve({
  "/articles": handleArticles,
});

interface ArticleData {
  source?: string
  country?: string
  exchange?: string
  title?: string
  description?: string
  author?: string
  url?: string
  company?: string
}

interface FaunaArticleResp extends Partial<ArticleData> {
  errors?: FaunaError[]
}

async function handleArticles(request: Request) {
  // We allow GET requests and POST requests with the
  // following fields (quite, author) in the body.
  const { error, body } = await validateRequest(request, {
    GET: {},
    POST: {
      body: ["source", "title", "description", "url"],
    },
  });
  // validateRequest populates the error if the request doesn't meet
  // the schema we defined.
  if (error) {
    return json({ error: error.message }, { status: error.status });
  }
  
  // Handle POST requests.
  if (request.method === "POST") {
    // make sure the article doesnt already exists
    const {url: incomingUrl = ""} = body as ArticleData;
    if (incomingUrl) {
      const articlesData = await getArticleByUrl(incomingUrl)
      console.log(articlesData)
      if (articlesData?.articles && articlesData?.articles?.length > 0) {
        return json({ warning: "article already exists" }, { status: 200 });
      }
    }
    // getArticleByUrl
    const { url, author, source, description, title, errors } = await createArticle(
      body as ArticleData,
    );
    if (errors) {
      console.error(errors.map((error) => error.message).join("\n"));
      return json({ error: "couldnt create the article" }, { status: 500 });
    }

    return json({ url, source, description, title, author }, { status: 201 });
  }

  // Handle GET requests.
  {
    const u = new URL(request.url);
    const size = u.searchParams.get('size');
    const cursor = u.searchParams.get('cursor');
    let articleData, errors;
    if (size) {
      const articles = await getArticles(size, "");
      articleData = articles.articles;
      errors = articles.errors;
    } else if(size && cursor) {
      const articles = await getArticles(size, cursor);
      articleData = articles.articles;
      errors = articles.errors;
    } else {
      const articles = await getArticles();
      articleData = articles.articles;
      errors = articles.errors;
    }
    if (errors) {
      console.error(errors.map((error) => error.message).join("\n"));
      return json({ error: "couldn't fetch the quotes" }, { status: 500 });
    }

    return json({ articles: articleData });
  }
}

async function getArticleByUrl(url: string) {
  let query = `
    query($url: String!) {
      getArticleByUrl(url: $url) {
        data {
          url
          source
          title
          description
        }
      }
    }
  `

  const { data, errors } = await queryFauna(query, {url});
  if (errors) {
    return { errors };
  }

  const {
    getArticleByUrl: { data: articles },
  } = data as { getArticleByUrl: { data: Partial<ArticleData>[] } };

  return { articles };
}
/** Get all quotes available in the database. */
async function getArticles(size: number | string = 0, cursor = "") {
  let query = "";
  if (size) {
    query = `
      query {
        allArticles(_size: ${size}) {
          data {
            _id
            source
            country
            exchange
            title
            description
            author
            url
            company
          }
        }
      }
    `
  } else if (size && cursor) {
    query = `
      query {
        allArticles(_size: ${size}, _cursor: ${cursor}) {
          data {
            _id
            source
            country
            exchange
            title
            description
            author
            url
            company
          }
        }
      }
    `
  } 
   else {
    // get all articles
    query = `
      query {
        allArticles {
          data {
            _id
            source
            country
            exchange
            title
            description
            author
            url
            company
          }
        }
      }
  `;
  }

  const { data, errors } = await queryFauna(query, {});
  if (errors) {
    return { errors };
  }

  const {
    allArticles: { data: articles },
  } = data as { allArticles: { data: Partial<ArticleData>[] } };

  return { articles };
}

/** Create a new quote in the database. */
async function createArticle({
  source,
  country,
  exchange,
  title,
  description,
  author,
  url,
  company
}: ArticleData): Promise<FaunaArticleResp> {
  const query = `
    mutation(
      $source: String!,
      $country: String,
      $exchange: String,
      $title: String!,
      $description: String!,
      $author: String,
      $url: String!,
      $company: String
    ) {
      createArticle(data: { 
        source: $source,
        country: $country,
        exchange: $exchange,
        title: $title,
        description: $description,
        author: $author,
        url: $url,
        company: $company
      }) {
        _id
        source
        country
        exchange
        title
        description
        author
        url
        company
      }
    }
  `;

  const { data, errors } = await queryFauna(query, {
    source,
    country,
    exchange,
    title,
    description,
    author,
    url,
    company
  });
  if (errors) {
    return { errors };
  }

  const { createArticle } = data as {
    createArticle: ArticleData;
  };

  return createArticle; // {quote: "*", author: "*"}
}

type FaunaError = {
  message: string;
};

/** Query FaunaDB GraphQL endpoint with the provided query and variables. */
async function queryFauna(
  query: string,
  variables: { [key: string]: unknown },
): Promise<{
  data?: unknown;
  errors?: FaunaError[];
}> {
  // Grab the secret from the environment.
  const token = Deno.env.get("FAUNA_SECRET");
  if (!token) {
    throw new Error("environment variable FAUNA_SECRET not set");
  }
  try {
    const res = await fetch("https://graphql.us.fauna.com/graphql", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        variables,
      }),
    });

    const { data, errors } = await res.json();
    if (errors) {
      // Return the first error if there are any.
      return { data, errors };
    }

    return { data };
  } catch (error) {
    return { errors: [{ message: "failed to fetch data from fauna" }] };
  }
}

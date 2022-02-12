import {
  json,
  serve,
  validateRequest,
} from "https://deno.land/x/sift@0.4.3/mod.ts";

import { dotEnvConfig } from './deps.ts';
 
console.log(dotEnvConfig({ export: true }));

serve({
  "/quotes": handleQuotes,
});

async function handleQuotes(request: Request) {
  // We allow GET requests and POST requests with the
  // following fields (quite, author) in the body.
  const { error, body } = await validateRequest(request, {
    GET: {},
    POST: {
      body: ["quote", "author"],
    },
  });
  // validateRequest populates the error if the request doesn't meet
  // the schema we defined.
  if (error) {
    return json({ error: error.message }, { status: error.status });
  }

  // Handle POST requests.
  if (request.method === "POST") {
    const { quote, author, errors } = await createQuote(
      body as { quote: string; author: string },
    );
    if (errors) {
      console.error(errors.map((error) => error.message).join("\n"));
      return json({ error: "couldn't create the quote" }, { status: 500 });
    }

    return json({ quote, author }, { status: 201 });
  }

  // Handle GET requests.
  {
    const { quotes, errors } = await getAllQuotes();
    if (errors) {
      console.error(errors.map((error) => error.message).join("\n"));
      return json({ error: "couldn't fetch the quotes" }, { status: 500 });
    }

    return json({ quotes });
  }
}

/** Get all quotes available in the database. */
async function getAllQuotes() {
  const query = `
    query {
      allQuotes {
        data {
          quote
          author
        }
      }
    }
  `;

  const { data, errors } = await queryFauna(query, {});
  if (errors) {
    return { errors };
  }

  const {
    allQuotes: { data: quotes },
  } = data as { allQuotes: { data: string[] } };

  return { quotes };
}

/** Create a new quote in the database. */
async function createQuote({
  quote,
  author,
}: {
  quote: string;
  author: string;
}): Promise<{ quote?: string; author?: string; errors?: FaunaError[] }> {
  const query = `
    mutation($quote: String!, $author: String!) {
      createQuote(data: { quote: $quote, author: $author }) {
        _id
        quote
        author
      }
    }
  `;

  const { data, errors } = await queryFauna(query, { quote, author });
  if (errors) {
    return { errors };
  }

  const { createQuote } = data as {
    createQuote: {
      quote: string;
      author: string;
    };
  };

  return createQuote; // {quote: "*", author: "*"}
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
    // Make a POST request to fauna's graphql endpoint with body being
    // the query and its variables.
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

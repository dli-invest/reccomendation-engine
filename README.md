# reccomendation-engine
stock recommendation engine based on all my stonk data.

fauna db is the file that stores all the ai data coming from my cron jobs (thanks github actions)

```js
/home/codespace/.deno/bin/deno run --allow-env --allow-net --allow-read fauna.ts
```

## Fields

* source (dli_invest)
* country (what country the company is in)
* exchange
* description
* author
* fields
* subjectivity
* senitment
* company (boolean)
* category
  * useless
  * unrelated
  * maybe
  * useful
  * excellent
  * expeditious


Rename to classify engine to classify news items as they come in.

## Graph ql structure

Sample graphql structure 

```gql
type Field {
  name: String!
  value: String!
  article: [Article!] @relation(name: "article")
} 

type Article {
  source: String!
  country: String!
  exchange: String!
  description: String!
  author: String!
  url: String!
  company: String!
  fields: [Field!] @relation(name: "fields")
}


type Query {
  allArticles: [Article!]
}
```



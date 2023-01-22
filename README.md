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
* category (0-10)
  * useless
  * unrelated
  * maybe
  * useful
  * excellent
  * expeditious


Rename to classify engine to classify news items as they come in.


## Autoclassify logic

Purge documents that are not interesting to me, logic.

Typical Tasks is 5, anything exciting is rated from 6 to 10

Dividends - 3
Earnings - 5
Rest - 0
Motley Fool, Zacks, Simply Wall Street - 2
Bloomberg - 3
Extension to File Form - 4
Earnings Call Transcript - 5
initial public offer - 2 or 3
private placement - 2
made an offer, acquisiton - 5
Beat Analyst Forecasts - 3
termination, bid together
rate hikes & fed 7
S&P 500
Any tickers gives 1 point automatically
People like elon musk and nhtsa
Supply Chain
Federal Trade Commission
CNW Group

Extract first few words with -
number with deal.


Any numbers above 0.9 in subjectivity, or senitment

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



## References 

Random nonsense

https://github.com/dli-invest/reccomendation-engine/compare/b45d711bb35ad3a39de102cf9d0bec4f37d0238e...main

in order to compare and see if I made any code changes, I used the built in github functionality.

See more projects at friendlyuser.github.io or dli-invest.github.io
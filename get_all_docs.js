const faunadb = require('faunadb')
const fs = require("fs")
const q = faunadb.query

const client = new faunadb.Client({
    secret: "fnAEfQf_giAAQkttjiTG2PD0vBzOV1LnzcTok6np",
    domain: "db.us.fauna.com"
  }) 
const dataObjects = []
function arrayToCSV(objArray) {
    const array = typeof objArray !== 'object' ? JSON.parse(objArray) : objArray;
    let str = `${Object.keys(array[0]).map(value => `"${value}"`).join(",")}` + '\r\n';

    return array.reduce((str, next) => {
        str += `${Object.values(next).map(value => `"${value}"`).join(",")}` + '\r\n';
        return str;
       }, str);
}

client.query(
    q.Map(
        q.Paginate(q.Documents(q.Collection("Article")), {size: 10000000}),
        q.Lambda(x => q.Get(x))
      )
).then(resp => {
    const data = resp.data
    data.forEach(element => {
        dataObjects.push(element.data)
    })
    fs.writeFile('data.json', JSON.stringify(dataObjects), err => {
        if (err) {
          console.error(err)
          return
        }
        //file written successfully
      })
      
})


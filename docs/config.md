# Configure hledger-lots

Hledger configuration is inserted directly into the journal using a custom format composed by key/value pairs that belongs to a namespace. This packages uses properties on **hledger-lots** namespace. 

## Configuration Format

Configuration is added on a row in the journal starting with '#+[namespace]' and multiple key value/pairs separated by commas. Properties can be spread into different rows with the same namespace

```text
#+namespace key1:value1, key:value2
#+namespace key3:value3
```

## Example

```text
#+hledger-lots avg_cost:true, check:true
#+hledger-lots no_desc:opening|closing
```

## hledger-lots properties

| Property | Allowed values | Description                                                                                                                                                                                                                                                                |
|----------|----------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| avg_cost | true or false  | true: uses average cost <br/>false: uses FIFO method                                                                                                                                                                                                                          |
| check    | true or false   | true: check if sale transaction uses the correct cost methods <br/>false: doesn't do cost method checks                                                                                                                                                                                                               |
| no_desc  | [regex]        | Description to be filtered out from calculation. Needed when closing journal with '--show-costs' option. Works like: 'not:desc:<value>'. If closed with default description, the value of this option should be: 'opening\|closing balances' |






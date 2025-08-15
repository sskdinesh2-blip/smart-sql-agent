\# Smart SQL Agent API



\## Endpoints



\### POST /sql/generate

Generate SQL from natural language



\*\*Request:\*\*

```json

{

&nbsp; "requirement": "Show top customers by revenue",

&nbsp; "schema\_info": "customers(id, name), orders(id, customer\_id, amount)"

}


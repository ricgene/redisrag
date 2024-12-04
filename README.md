# Redis Rag Chat


Redis Rag Chat is a simple Chat application demonstrating how to use the RAG pattern with various frameworks using Redis as your Vector Database.
For our example, the default chat type is a conversation with an intelligent agent that can recommend different beers to you, however
swapping that out with whatever other RAG operation you want is as simple as updating the SystemPrompt and changing out the documents you
store in your Redis Database.

## Running with docker compose

There are several component parts of this demo, to run them all with docker-compose, just run:

```sh
OpenAIApiKey=<YOUR_OPENAI_API_KEY> docker compose up
```

## Running the individual parts separately

You can also run each component part of this same separately

### Frontend

```
cd common/frontend
npm install
npm start
```

### Backend

#### Configuration

change directory into the `backend/webapi` directory. Then run the following command: 

```sh
mv .env.sample .env
```

And change the `OPENAI_API_KEY` to your Open AI API key

#### Running the backend

To run the app, now just run:

```
poetry start run
```

## Adding Documents to your Redis Database

After the application is started, in order to make it useful you need to add documents to Redis. For this example we've provided
a dataset of beers that you can upload to Redis, and then ask the bot for recommendations.

### Upload the Provided Data

To upload the provided Data just run `./scripts/setup_beers.sh`

### Bring your own data

If you want to bring your own data files to add to Redis, you can do so by using the `scripts/upload.sh`, 
passing in the directory where your files are as the first argument, and then optionally passing in a `limit` for the number of files you want 
to upload and an optional `url` argument to define the upload URL.

## Accessing the Site

After the frontend and backend are running, you can access the site on `localhost:3000`
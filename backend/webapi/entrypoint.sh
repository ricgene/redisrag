ENV_FILE=".env"
mv .env.sample $ENV_FILE

if [ -z "$OpenAIApiKey" ]; then
    echo "Error: OpenAIApiKey environment variable is not set."
    exit 1
fi

sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=${OpenAIApiKey}/" "$ENV_FILE"

cat .env

poetry run start
ENV_FILE=".env"
mv .env.docker $ENV_FILE

if [ -z "$OpenAIApiKey" ]; then
    echo "Error: OpenAIApiKey environment variable is not set."
    exit 1
fi

sed -i "s/^OPENAI_API_KEY=.*/OPENAI_API_KEY=${OpenAIApiKey}/" "$ENV_FILE"
sed -i "s/^KERNEL_MEMORY_URL=.*KERNEL_MEMORY_URL=http://localhost:9001" "$ENV_FILE"

cat .env

poetry run start
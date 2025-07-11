**RESPONSE**
```json
{
  "advancedContent": {
    "content": "こんにちは、おはようございます。今日はいい天気ですね。おはようございます、元気ですか？",
    "explanation": "This is a friendly greeting that includes both 'good morning' and 'hello'. It's a common way to start a conversation in Japanese, often used in business or social settings. The phrase '今日はいい天気ですね' tto 'The weather is nice today,' and 'おはようございます、元気ですか？' means 'Good morning, are you well?' This is a natural way to greet someone and start a conversation."
  },
  "directTranslation": "こんにちは",
  "practicalUsage": [
    {
      "translation": "Hello, how are you?",
      "usage": "こんにちは、どうですか？"
    },
    {
      "translation": "Good morning, do your best today.",
      "usage": "おはようございます、今日も頑張ってください。"
    },
    {
      "translation": "Hello, the weather is good today.",
      "usage": "こんにちは、今日は天気が良いです。"
    }
  ],
  "relatedVocabulary": [
    {
      "translation": "first time meeting",
      "vocabulary": "はじめまして"
    },
    {
      "translation": "good morning",
      "vocabulary": "おはようございます"
    },
    {
      "translation": "hello",
      "vocabulary": "こんにちは"
    }
  ]
}
```
**REQUEST**
```shell
curl -X POST http://localhost:5001/api/lesson \
-H "Content-Type: application/json" \
-d '{
"word": "good morning",
"foreignLanguage": "Japanese"
}' | jq '.'
```


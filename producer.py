from kafka import KafkaProducer
import tweepy
import json


BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAAO35ygEAAAAAKq3X5JB%2F0xBgr5Gma%2FxXTRh%2BYXw%3DoyyfdvloWZGXXIwxzD58j2UWKJEXkg1zt47VwF9HbKGWZPJP8J"
client = tweepy.Client(bearer_token=BEARER_TOKEN)

# Configurar Kafka Producer
producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

# Definir palavra-chave para busca
query = "tecnologia -is:retweet"

def coletar_tweets():
    tweets = client.search_recent_tweets(query=query, tweet_fields=["created_at"], max_results=10)
    for tweet in tweets.data:
        mensagem = {"texto": tweet.text, "data": str(tweet.created_at)}
        producer.send("simple.elasticsearch.data", value=mensagem)
        print(f"Enviando tweet: {tweet.text}")

# Executar coleta de tweets
coletar_tweets()

# Fechar o Kafka Producer
producer.flush()
producer.close()

# import openai
# import json
# from kafka import KafkaProducer
# from pyspark.sql import SparkSession
# from pyspark.sql.functions import from_json, col
# from pyspark.sql.types import StructType, StringType

# # Configurar chave da API OpenAI
# openai.api_key = "SUA_OPENAI_API_KEY"

# # Criar sessão Spark
# spark = SparkSession.builder \
#     .appName("TwitterKafkaIA") \
#     .config("spark.sql.streaming.checkpointLocation", "/tmp") \
#     .getOrCreate()

# # Definir esquema dos tweets
# tweet_schema = StructType() \
#     .add("texto", StringType()) \
#     .add("data", StringType())

# # Criar um consumidor Kafka
# df = spark.readStream \
#     .format("kafka") \
#     .option("kafka.bootstrap.servers", "localhost:9092") \
#     .option("subscribe", "tweets_topic") \
#     .option("startingOffsets", "earliest") \
#     .load()

# # Converter JSON para DataFrame
# tweets_df = df.selectExpr("CAST(value AS STRING)") \
#     .select(from_json(col("value"), tweet_schema).alias("data")) \
#     .select("data.*")

# # Criar Kafka Producer para enviar as respostas da IA para o Kafka
# producer = KafkaProducer(
#     bootstrap_servers="localhost:9092",
#     value_serializer=lambda x: json.dumps(x).encode('utf-8')
# )

# def processar_com_ia(texto):
#     """ Envia o tweet para a OpenAI e recebe a análise """
#     prompt = f"Analise o seguinte tweet e forneça um resumo e uma classificação de sentimento (positivo, neutro ou negativo): {texto}"
    
#     resposta = openai.ChatCompletion.create(
#         model="gpt-4",
#         messages=[{"role": "user", "content": prompt}]
#     )
    
#     return resposta["choices"][0]["message"]["content"]

# def enviar_para_kafka(mensagem):
#     """ Envia o resultado da IA para o Kafka no tópico 'canal_output' """
#     producer.send("canal_output", value=mensagem)

# # Aplicar processamento IA em cada tweet e enviar para Kafka
# query = tweets_df.writeStream \
#     .foreachBatch(lambda batch_df, _: [
#         enviar_para_kafka({
#             "tweet_original": row["texto"],
#             "resumo": processar_com_ia(row["texto"]),
#             "data": row["data"]
#         }) for row in batch_df.collect()
#     ]) \
#     .start()

# query.awaitTermination()

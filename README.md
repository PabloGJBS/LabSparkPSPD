# Laboratório Spark Streaming com Kafka e Twitter

Este repositório contém a implementação de um pipeline de processamento de dados em tempo real utilizando **Apache Kafka**, **Apache Spark**, e a API do **Twitter/X**. O objetivo é coletar tweets em tempo real, processá-los com Spark Streaming e exibir resultados em um dashboard gráfico.

## Participantes 

|                  nome                  | matricula |
| :------------------------------------: | :-------: |
|      Arthur Taylor de Jesus Popov      | 190084642 |
|      João Lucas Pinto Vasconcelos      | 190089601 |
| Pablo Guilherme de Jesus Batista Silva | 200025791 |
|     Pedro Lucas Siqueira Fernande      | 190115564 |

## Índice
- [Laboratório Spark Streaming com Kafka e Twitter](#laboratório-spark-streaming-com-kafka-e-twitter)
  - [Participantes](#participantes)
  - [Índice](#índice)
  - [Descrição do Projeto](#descrição-do-projeto)
  - [Pré-requisitos](#pré-requisitos)
  - [Passo a Passo da Configuração](#passo-a-passo-da-configuração)
    - [Configuração do Ambiente Local](#configuração-do-ambiente-local)
    - [Coleta de Tweets com Kafka Producer](#coleta-de-tweets-com-kafka-producer)
    - [Processamento com Spark Streaming](#processamento-com-spark-streaming)
  - [Executando o Pipeline](#executando-o-pipeline)
  - [Configurando o Conector Kafka Connect para Elasticsearch](#configurando-o-conector-kafka-connect-para-elasticsearch)
    - [Passos para Configurar o Conector](#passos-para-configurar-o-conector)
  - [Migrando para Google Colab](#migrando-para-google-colab)
  - [Referências](#referências)

---

## Descrição do Projeto

O objetivo deste laboratório é criar um sistema de processamento de dados em tempo real que:
1. Coleta tweets de uma rede social (Twitter/X) usando sua API.
2. Envia esses tweets para um tópico Kafka.
3. Processa os tweets com Spark Streaming para contar a frequência das palavras.
4. Exibe os resultados em um dashboard gráfico (usando ElasticSearch e Kibana).

---

## Pré-requisitos

Para executar este projeto, você precisará dos seguintes componentes instalados em sua máquina:
- **Python 3.x**
- **Apache Kafka** ([Download](https://kafka.apache.org/downloads))
- **Apache Spark** ([Download](https://spark.apache.org/downloads.html))
- **Bibliotecas Python**:
  ```bash
  pip install tweepy kafka-python pyspark
  ```
- **API do Twitter/X**: Um token de acesso válido para a API do Twitter/X. Obtenha seu `BEARER_TOKEN` no [Twitter Developer Portal](https://developer.twitter.com/).

---

## Passo a Passo da Configuração

### Configuração do Ambiente Local

1. **Instalar o Apache Kafka**:
   - Baixe a versão mais recente do Kafka no site oficial: [Kafka Downloads](https://kafka.apache.org/downloads).
   - Extraia o arquivo em um diretório de sua escolha.
   - Inicie o **Zookeeper** e o **Kafka Broker**:
     ```bash
     # Iniciar o Zookeeper
     bin/zookeeper-server-start.sh config/zookeeper.properties
     
     # Em outro terminal, iniciar o servidor Kafka
     bin/kafka-server-start.sh config/server.properties
     ```

2. **Criar um Tópico Kafka**:
   - Crie um tópico chamado `tweets_topic`:
     ```bash
     bin/kafka-topics.sh --create --topic tweets_topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
     ```

---

### Coleta de Tweets com Kafka Producer

1. **Instale as bibliotecas necessárias**:
   ```bash
   pip install tweepy kafka-python
   ```

2. **Crie o Produtor Kafka**:
   - Crie um arquivo `producer.py` com o código abaixo:
     ```python
     from kafka import KafkaProducer
     import tweepy
     import json
     # Configuração da API do Twitter
     BEARER_TOKEN = "SEU_BEARER_TOKEN"
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
             producer.send("tweets_topic", value=mensagem)
             print(f"Enviando tweet: {tweet.text}")
     # Executar coleta de tweets
     coletar_tweets()
     # Fechar o Kafka Producer
     producer.flush()
     producer.close()
     ```

3. **Execute o Produtor**:
   ```bash
   python producer.py
   ```

---

### Processamento com Spark Streaming

1. **Instale o Apache Spark**:
   - Baixe a versão 3.2.1 do Spark com Hadoop 3.2: [Spark Downloads](https://spark.apache.org/downloads.html).
   - Configure as variáveis de ambiente:
     ```bash
     export SPARK_HOME=~/spark-3.2.1-bin-hadoop3.2
     export PATH=$SPARK_HOME/bin:$PATH
     ```

2. **Crie o Consumidor Kafka com Spark Streaming**:
   - Crie um arquivo `consumer_spark.py` com o código abaixo:
     ```python
     from pyspark.sql import SparkSession
     from pyspark.sql.functions import from_json, col, explode, split
     from pyspark.sql.types import StructType, StringType
     # Criar sessão Spark
     spark = SparkSession.builder \
         .appName("TwitterKafkaStreaming") \
         .config("spark.sql.streaming.checkpointLocation", "/tmp") \
         .getOrCreate()
     # Definir esquema dos tweets
     tweet_schema = StructType() \
         .add("texto", StringType()) \
         .add("data", StringType())
     # Ler dados do Kafka
     df = spark.readStream \
         .format("kafka") \
         .option("kafka.bootstrap.servers", "localhost:9092") \
         .option("subscribe", "tweets_topic") \
         .option("startingOffsets", "earliest") \
         .load()
     # Converter JSON para DataFrame
     tweets_df = df.selectExpr("CAST(value AS STRING)").select(from_json(col("value"), tweet_schema).alias("data")).select("data.*")
     # Contar palavras mais frequentes
     palavras_df = tweets_df.select(explode(split(col("texto"), " ")).alias("palavra"))
     contagem_palavras = palavras_df.groupBy("palavra").count().orderBy(col("count").desc())
     # Exibir no console
     query = contagem_palavras.writeStream \
         .outputMode("complete") \
         .format("console") \
         .start()
     query.awaitTermination()
     ```

3. **Execute o Consumidor**:
   ```bash
   python consumer_spark.py
   ```

---

## Executando o Pipeline

1. **Iniciar o Kafka**:
   ```bash
   # Iniciar o Zookeeper
   bin/zookeeper-server-start.sh config/zookeeper.properties
   
   # Iniciar o Kafka Broker
   bin/kafka-server-start.sh config/server.properties
   ```

2. **Criar o Tópico Kafka**:
   ```bash
   bin/kafka-topics.sh --create --topic tweets_topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
   ```

3. **Rodar o Produtor Kafka**:
   ```bash
   python producer.py
   ```

4. **Rodar o Consumidor Kafka com Spark**:
   ```bash
   python consumer_spark.py
   ```

---

## Configurando o Conector Kafka Connect para Elasticsearch

Para integrar os dados processados pelo Spark Streaming ao **Elasticsearch** e visualizá-los no **Kibana**, é necessário configurar um **conector Kafka Connect**. Este conector enviará os dados do tópico Kafka para o Elasticsearch.

### Passos para Configurar o Conector

1. **Certifique-se de que o Elasticsearch e o Kibana estão instalados e rodando**:
   - O Elasticsearch deve estar acessível em `http://localhost:9200`.
   - O Kibana deve estar acessível em `http://localhost:5601`.

2. **Inicie o Kafka Connect**:
   - O Kafka Connect é uma ferramenta que permite a integração entre Kafka e outros sistemas, como o Elasticsearch.
   - Certifique-se de que o Kafka Connect está rodando. Você pode iniciar o Kafka Connect em modo standalone ou distribuído. Para este exemplo, usaremos o modo distribuído.

   ```bash
   # Iniciar o Kafka Connect em modo distribuído
   bin/connect-distributed.sh config/connect-distributed.properties
   ```

3. **Crie o Conector Elasticsearch**:
   - Use o comando `curl` para criar um conector Kafka Connect que envie os dados do tópico Kafka para o Elasticsearch.

   ```bash
   curl -X POST -H "Content-Type: application/json" --data '{
     "name": "elasticsearch-sink",
     "config": {
       "connector.class": "io.confluent.connect.elasticsearch.ElasticsearchSinkConnector",
       "tasks.max": "1",
       "topics": "tweets_topic",
       "key.ignore": "true",
       "connection.url": "http://localhost:9200",
       "type.name": "kafka-connect"
     }
   }' http://localhost:8083/connectors
   ```

4. **Verifique o Status do Conector**:
   - Após criar o conector, você pode verificar seu status usando o seguinte comando:

   ```bash
   curl http://localhost:8083/connectors/elasticsearch-sink/status
   ```

5. **Visualize os Dados no Kibana**:
   - Abra o Kibana (`http://localhost:5601`) e crie um índice no Elasticsearch para os dados do tópico Kafka.
   - Crie visualizações e dashboards no Kibana para exibir os dados processados.

---

## Migrando para Google Colab

Se desejar migrar o projeto para o Google Colab, siga estas etapas:
1. Altere a conexão com o Kafka para usar um serviço gerenciado, como **Confluent Cloud** ou **Redpanda**.
2. Adapte o código para funcionar no ambiente do Colab, instalando as dependências necessárias via células de código.

---

## Referências

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Apache Spark Documentation](https://spark.apache.org/docs/latest/)
- [Twitter Developer Portal](https://developer.twitter.com/)
- [ElasticSearch and Kibana](https://www.elastic.co/pt/elasticsearch)

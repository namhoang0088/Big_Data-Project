const express = require('express');
const http = require('http');
const { Kafka } = require('kafkajs');
const path = require('path');

const app = express();
const server = http.createServer(app);

const kafka = new Kafka({
  clientId: 'my-consumer',
  brokers: ['localhost:9092', 'localhost:9093', 'localhost:9094'],
});

const consumer = kafka.consumer({
  groupId: 'my-group',
});

let clients = [];

const iconPath = path.join(__dirname, 'icon');
app.use('/icon', express.static(iconPath));

app.get('/', (req, res) => {
    res.sendFile(__dirname + '/test.html');
});

app.get('/events', async (req, res) => {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    clients.push(res);

    req.on('close', () => {
        clients = clients.filter(client => client !== res);
    });
});

const runConsumer = async () => {
    await consumer.connect();

    const coinTopics = ['BTC', 'ETH', 'XRP', 'BCH', 'LTC', 'ADA', 'DOT', 'BNB', 'LINK', 'XLM'];
    await Promise.all(coinTopics.map(topic => consumer.subscribe({ topic })));

    await consumer.run({
        eachMessage: async ({ topic, partition, message }) => {
            const coinPrice = message.value.toString();
            console.log(topic, coinPrice);

            clients.forEach(client => {
                client.write(`data: ${JSON.stringify({ coin: topic, price: coinPrice })}\n\n`);
            });
        },
    });
};

const PORT = process.env.PORT || 5500;
server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    
    runConsumer().catch(error => {
        console.error('Error starting Kafka consumer:', error);
        process.exit(1);
    });
});

consumer.on('consumer.crash', (err) => {
    console.error('Consumer crashed:', err);
    process.exit(1);
});

process.on('SIGINT', async () => {
    await consumer.disconnect();
    console.log('Consumer disconnected');
    process.exit(0);
});

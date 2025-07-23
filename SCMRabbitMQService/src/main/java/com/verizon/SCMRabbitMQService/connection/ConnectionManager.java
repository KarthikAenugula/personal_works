package com.verizon.SCMRabbitMQService.connection;

import javax.net.ssl.SSLContext;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.KeyManagerFactory;

import jakarta.xml.bind.JAXBContext;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.security.KeyStore;
import java.util.*;

import com.rabbitmq.client.Connection;
import com.rabbitmq.client.ConnectionFactory;
import com.verizon.SCMRabbitMQService.model.MQueue;
import com.verizon.SCMRabbitMQService.model.MQueues;

public class ConnectionManager {

    public static Map<String, Connection> producerConnections = new HashMap<>();
    public static Map<String, Connection> consumerConnections = new HashMap<>();

    public static void initializeConnections(String xmlPath) throws Exception {
        JAXBContext context = JAXBContext.newInstance(MQueues.class);
        MQueues mQueues = (MQueues) context.createUnmarshaller().unmarshal(new File(xmlPath));

        for (MQueue mq : mQueues.getMQueues()) {
            if (!"Y".equalsIgnoreCase(mq.getIsRabbitMq())) continue;

            ConnectionFactory factory = new ConnectionFactory();
            factory.setHost(mq.getConnectionFactory().getHost());
            factory.setPort(mq.getConnectionFactory().getPort());
            factory.setVirtualHost(mq.getConnectionFactory().getVirtualHost());
            factory.setUsername(readValueFromFile(mq.getQueueUserName()));
            factory.setPassword(readValueFromFile(mq.getQueuePassword()));

            if ("Y".equalsIgnoreCase(mq.getSslEnabled())) {
                SSLContext sslContext = SSLContext.getInstance(mq.getTlsVersion());
                KeyStore ks = KeyStore.getInstance("JKS");

                ks.load(new FileInputStream(mq.getSslCertificatePath()),
                        readValueFromFile(mq.getTrustStorePassphrase()).toCharArray());

                KeyManagerFactory kmf = KeyManagerFactory.getInstance("SunX509");
                kmf.init(ks, readValueFromFile(mq.getTrustStorePassphrase()).toCharArray());

                TrustManagerFactory tmf = TrustManagerFactory.getInstance("SunX509");
                tmf.init(ks);

                sslContext.init(kmf.getKeyManagers(), tmf.getTrustManagers(), null);
                factory.useSslProtocol(sslContext);
            }

            Connection conn = factory.newConnection();
            if ("Y".equalsIgnoreCase(mq.getSender())) {
                producerConnections.put(mq.getDestinationAppID(), conn);
                ChannelPoolManager.initializeProducerPool(mq.getDestinationAppID(), conn);
            } else {
                consumerConnections.put(mq.getDestinationAppID(), conn);
                ChannelPoolManager.initializeConsumerPool(mq.getDestinationAppID(), conn);
            }
        }
    }

    private static String readValueFromFile(String path) throws IOException {
        return new String(Files.readAllBytes(Paths.get(path))).trim();
    }

    public static Connection getProducerConnection(String key) {
        return producerConnections.get(key);
    }

    public static Connection getConsumerConnection(String key) {
        return consumerConnections.get(key);
    }
}
package com.verizon.SCMRabbitMQService.connection;

import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Channel;

import java.nio.charset.StandardCharsets;

public class Producer {
    public static void sendMessage(String destinationAppId, String queueName,
                                   String exchange, String routingKey, String message) {
        try {
            Channel channel = ChannelPoolManager.borrowProducerChannel(destinationAppId);
            AMQP.BasicProperties props = new AMQP.BasicProperties.Builder()
                    .contentType("application/json")
                    .deliveryMode(2) // persistent
                    .build();
            channel.basicPublish(exchange, routingKey, props, message.getBytes(StandardCharsets.UTF_8));
            System.out.println("Produced message to " + queueName);
            ChannelPoolManager.returnProducerChannel(destinationAppId, channel);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}


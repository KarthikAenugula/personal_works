package com.verizon.SCMRabbitMQService.connection;

import com.rabbitmq.client.Channel;

import java.nio.charset.StandardCharsets;

public class Consumer {
    public static void receiveMessages(String destinationAppID, String queueName) {
        try {
            Channel channel = ChannelPoolManager.borrowConsumerChannel(destinationAppID);
            channel.basicConsume(queueName, true, (tag, delivery) -> {
                String msg = new String(delivery.getBody(), StandardCharsets.UTF_8);
                System.out.println("[x] Received: " + msg);
            }, tag -> {
            });
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}


package com.verizon.SCMRabbitMQService.connection;

import com.rabbitmq.client.Channel;
import com.rabbitmq.client.Connection;

import java.util.concurrent.*;

public class ChannelPoolManager {
    private static final int POOL_SIZE = 10;

    private static final ConcurrentHashMap<String, BlockingQueue<Channel>> producerPools = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, BlockingQueue<Channel>> consumerPools = new ConcurrentHashMap<>();

    public static void initializeProducerPool(String id, Connection conn) throws Exception {
        BlockingQueue<Channel> pool = new ArrayBlockingQueue<>(POOL_SIZE);
        for (int i = 0; i < POOL_SIZE; i++) {
            pool.put(conn.createChannel());
        }
        producerPools.put(id, pool);
    }

    public static void initializeConsumerPool(String id, Connection conn) throws Exception {
        BlockingQueue<Channel> pool = new ArrayBlockingQueue<>(POOL_SIZE);
        for (int i = 0; i < POOL_SIZE; i++) {
            pool.put(conn.createChannel());
        }
        consumerPools.put(id, pool);
    }

    public static Channel borrowProducerChannel(String id) throws InterruptedException {
        return producerPools.get(id).take();
    }

    public static void returnProducerChannel(String id, Channel channel) throws InterruptedException {
        producerPools.get(id).put(channel);
    }

    public static Channel borrowConsumerChannel(String id) throws InterruptedException {
        return consumerPools.get(id).take();
    }

    public static void returnConsumerChannel(String id, Channel channel) throws InterruptedException {
        consumerPools.get(id).put(channel);
    }
}

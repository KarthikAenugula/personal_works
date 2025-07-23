package com.verizon.SCMRabbitMQService.model;

import jakarta.xml.bind.annotation.*;

import java.util.List;

import com.rabbitmq.client.ConnectionFactory;

@XmlAccessorType(XmlAccessType.FIELD)
public class MQueue {
    @XmlAttribute
    private String sender;

    @XmlAttribute
    private String isRabbitMq;

    @XmlAttribute
    private String destinationAppID;

    @XmlAttribute
    private String sslEnabled;

    @XmlElement(name = "ConnectionFactory")
    private ConnectionFactory connectionFactory;

    private String Exchange;
    private String RoutingKey;
    private String QueueName;
    private String QueueUserName;
    private String QueuePassword;
    private String SslCertificatePath;
    private String TrustStorePassphrase;
    private String TlsVersion;
    
	public String getExchange() {
		return Exchange;
	}
	public void setExchange(String exchange) {
		Exchange = exchange;
	}
	public String getRoutingKey() {
		return RoutingKey;
	}
	public void setRoutingKey(String routingKey) {
		RoutingKey = routingKey;
	}
	public String getQueueName() {
		return QueueName;
	}
	public void setQueueName(String queueName) {
		QueueName = queueName;
	}
	public String getQueueUserName() {
		return QueueUserName;
	}
	public void setQueueUserName(String queueUserName) {
		QueueUserName = queueUserName;
	}
	public String getQueuePassword() {
		return QueuePassword;
	}
	public void setQueuePassword(String queuePassword) {
		QueuePassword = queuePassword;
	}
	public String getSslCertificatePath() {
		return SslCertificatePath;
	}
	public void setSslCertificatePath(String sslCertificatePath) {
		SslCertificatePath = sslCertificatePath;
	}
	public String getTrustStorePassphrase() {
		return TrustStorePassphrase;
	}
	public void setTrustStorePassphrase(String trustStorePassphrase) {
		TrustStorePassphrase = trustStorePassphrase;
	}
	public String getTlsVersion() {
		return TlsVersion;
	}
	public void setTlsVersion(String tlsVersion) {
		TlsVersion = tlsVersion;
	}
	public String getSender() {
		return sender;
	}
	public void setSender(String sender) {
		this.sender = sender;
	}
	public String getIsRabbitMq() {
		return isRabbitMq;
	}
	public void setIsRabbitMq(String isRabbitMq) {
		this.isRabbitMq = isRabbitMq;
	}
	public String getDestinationAppID() {
		return destinationAppID;
	}
	public void setDestinationAppID(String destinationAppID) {
		this.destinationAppID = destinationAppID;
	}
	public String getSslEnabled() {
		return sslEnabled;
	}
	public void setSslEnabled(String sslEnabled) {
		this.sslEnabled = sslEnabled;
	}
	public ConnectionFactory getConnectionFactory() {
		return connectionFactory;
	}
	public void setConnectionFactory(ConnectionFactory connectionFactory) {
		this.connectionFactory = connectionFactory;
	}
	

    
}

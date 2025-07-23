package com.verizon.SCMRabbitMQService.model;

import java.util.List;

import jakarta.xml.bind.annotation.XmlAccessType;
import jakarta.xml.bind.annotation.XmlAccessorType;
import jakarta.xml.bind.annotation.XmlElement;
import jakarta.xml.bind.annotation.XmlRootElement;

@XmlRootElement(name = "MQueues")
@XmlAccessorType(XmlAccessType.FIELD)
public class MQueues {
	
 @XmlElement(name = "MQueue")
 private List<MQueue> mQueues;

 public List<MQueue> getMQueues() {
     return mQueues;
 }
 public void setMQueues(List<MQueue> mQueues) {
     this.mQueues = mQueues;
 }
 
}

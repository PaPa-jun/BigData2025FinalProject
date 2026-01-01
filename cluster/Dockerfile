FROM ubuntu:latest

# Set Timezone to Asia/Shanghai
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && echo "Asia/Shanghai" > /etc/timezone

# Install necessary packages
RUN apt-get update \
    && apt-get install -y \
    sudo \
    openjdk-8-jdk \
    ssh \
    pdsh \
    vim \
    wget \
    net-tools \
    procps \
    rsync \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Download and extract Hadoop
RUN mkdir -p /app \
    && cd /app \
    && wget https://dlcdn.apache.org/hadoop/common/stable/hadoop-3.4.2.tar.gz \
    && tar -zxzf hadoop-3.4.2.tar.gz \
    && rm hadoop-3.4.2.tar.gz

# Set environment variables
ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-arm64
ENV HADOOP_HOME=/app/hadoop-3.4.2
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin

# Configure SSH for passwordless login
RUN ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa \
    && cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys \
    && chmod 0600 ~/.ssh/authorized_keys

# Copy Hadoop configuration files
COPY ./configs/core-site.xml ${HADOOP_HOME}/etc/hadoop/core-site.xml
COPY ./configs/hdfs-site.xml ${HADOOP_HOME}/etc/hadoop/hdfs-site.xml
COPY ./configs/mapred-site.xml ${HADOOP_HOME}/etc/hadoop/mapred-site.xml
COPY ./configs/yarn-site.xml ${HADOOP_HOME}/etc/hadoop/yarn-site.xml
COPY ./scripts/hadoop-env.sh ${HADOOP_HOME}/etc/hadoop/hadoop-env.sh
COPY ./scripts/yarn-env.sh ${HADOOP_HOME}/etc/hadoop/yarn-env.sh

# Download and extract HBase
RUN cd /app \
    && wget https://dlcdn.apache.org/hbase/stable/hbase-2.5.13-bin.tar.gz \
    && tar -zxvf hbase-2.5.13-bin.tar.gz \
    && rm hbase-2.5.13-bin.tar.gz

# Set HBase environment variables
ENV HBASE_HOME=/app/hbase-2.5.13
ENV PATH=$PATH:$HBASE_HOME/bin

# Copy HBase configuration files
COPY ./scripts/hbase-env.sh ${HBASE_HOME}/conf/hbase-env.sh
COPY ./configs/hbase-site.xml ${HBASE_HOME}/conf/hbase-site.xml

# Expose necessary ports
EXPOSE 9870 8088 9000 9864 9866 9090 16010

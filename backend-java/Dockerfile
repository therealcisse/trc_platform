# Build
FROM maven:3.9.8-eclipse-temurin-21 AS build
WORKDIR /app
COPY pom.xml .
RUN mvn -q -e -DskipTests dependency:go-offline
COPY src ./src
RUN mvn -q -e -DskipTests package

# Run
FROM eclipse-temurin:21-jre
ENV JAVA_OPTS="-XX:+UseZGC -XX:+ZGenerational"
WORKDIR /app
COPY --from=build /app/target/*.jar /app/app.jar
USER 10001
EXPOSE 8080
ENTRYPOINT ["sh","-c","java $JAVA_OPTS -jar /app/app.jar"]


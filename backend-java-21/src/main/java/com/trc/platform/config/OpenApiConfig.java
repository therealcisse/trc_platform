package com.trc.platform.config;

import io.swagger.v3.oas.models.ExternalDocumentation;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {
    @Bean
    /** Field description. */
    public OpenAPI apiDocs() {
        return new OpenAPI()
                .info(
                        new Info()
                                .title("TRC Platform API")
                                .version("1.0.0")
                                .description("OpenAPI documentation for TRC Platform"))
                .externalDocs(new ExternalDocumentation().description("Product Requirements"));
    }
}

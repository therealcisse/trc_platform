package com.trc.platform;

import static org.assertj.core.api.Assertions.assertThat;

import com.trc.platform.core.controller.CoreController;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class SmokeTest {

    @Autowired CoreController coreController;

    @Test
    void contextLoads() {
        assertThat(coreController).isNotNull();
    }
}

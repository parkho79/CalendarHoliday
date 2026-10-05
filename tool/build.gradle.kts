import org.jetbrains.compose.desktop.application.dsl.TargetFormat

plugins {
    kotlin("jvm") version "2.2.20"
    kotlin("plugin.serialization") version "2.2.20"
    id("org.jetbrains.kotlin.plugin.compose") version "2.2.20"
    id("org.jetbrains.compose") version "1.7.3"
}

repositories {
    google()
    mavenCentral()
}

dependencies {
    implementation(compose.desktop.currentOs)
    implementation(compose.material3)
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-swing:1.9.0")
}

kotlin {
    jvmToolchain(17)
}

compose.desktop {
    application {
        mainClass = "MainKt"
        nativeDistributions {
            targetFormats(TargetFormat.Dmg, TargetFormat.Msi, TargetFormat.Deb)
            packageName = "HolidayCurator"
            packageVersion = "1.0.0"
        }
    }
}

// GUI 없이 핵심 로직만 검증하는 스모크 테스트 (SelfTest.kt 참고) — 읽기 전용이라 안전함.
tasks.register<JavaExec>("runSelfTest") {
    group = "verification"
    mainClass.set("SelfTestKt")
    classpath = sourceSets["main"].runtimeClasspath
}


/**
 * GUI 없이 핵심 로직(비 Compose 부분)만 검증하는 임시 스모크 테스트.
 * `./gradlew runSelfTest`로 실행. UI를 직접 조작할 수 없는 환경에서 Pipeline/AppleIcs/
 * Corrections가 실제로 동작하는지 확인하기 위한 용도 — 검증 끝나면 지워도 됨.
 */
fun main() {
    println("=== 1) Pipeline.countryList() ===")
    Pipeline.countryList()
        .onSuccess { println("성공: nager ${it.nager.size}개, google ${it.google.size}개") }
        .onFailure { println("실패: ${it.message}") }

    println()
    println("=== 2) Pipeline.regenerate(\"kr\") + readHolidayList ===")
    Pipeline.regenerate("kr")
        .onSuccess { println("재생성 성공") }
        .onFailure { println("재생성 실패: ${it.message}") }
    Pipeline.readHolidayList("kr")
        .onSuccess { println("읽기 성공: 2026년 ${it.holidays["2026"]?.size}건") }
        .onFailure { println("읽기 실패: ${it.message}") }

    println()
    println("=== 3) AppleIcs.fetch(\"kr\") ===")
    val apple = AppleIcs.fetch("kr")
    if (apple.error != null) {
        println("실패: ${apple.error}")
    } else {
        val years = apple.byYear.keys.sorted()
        println("성공: ${years.firstOrNull()}~${years.lastOrNull()} (${years.size}개 연도)")
        println("2026-03-01 -> ${apple.byYear["2026"]?.get("03-01")}")
    }

    println()
    println("=== 4) Corrections.rulesFor(\"kr\") (읽기 전용, 안 씀) ===")
    val rules = Corrections.rulesFor("kr")
    println("kr 규칙 ${rules.size}개, 첫 3개: ${rules.take(3)}")

    println()
    println("=== 전부 완료 ===")
}

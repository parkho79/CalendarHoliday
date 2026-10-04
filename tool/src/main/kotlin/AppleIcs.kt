import java.io.ByteArrayInputStream
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.time.Duration
import java.time.LocalDate
import java.time.DateTimeException
import java.util.zip.GZIPInputStream

/**
 * 애플 iCloud 캘린더가 공개 제공하는 공휴일 구독 피드(비공식, 문서화 안 됨 — 2026-10-01에
 * 발견). URL 패턴: https://calendars.icloud.com/holidays/{국가코드}_{언어코드}.ics
 * 이 도구에서만 참고/대조용으로 쓰고, 실제 파이프라인(update_holidays.py)은 절대 이걸
 * 자동으로 쓰지 않는다 — 공식 API가 아니라 예고 없이 막히거나 형식이 바뀔 수 있어서,
 * 실패하면 반드시 사용자가 눈치채야 함(조용히 다른 값으로 대체하지 않음).
 */
object AppleIcs {
    private val client: HttpClient = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .build()

    // 국가코드 -> 언어코드 추정값. 틀려도 애플이 404를 주고 그대로 에러로 보여질 뿐이라
    // 안전함(이름만 추정, 실제 데이터 로직은 아님).
    val LANG_GUESS: Map<String, String> = mapOf(
        "kr" to "ko", "jp" to "ja", "cn" to "zh", "hk" to "zh", "tw" to "zh",
        "id" to "id", "sg" to "en", "ph" to "en", "au" to "en", "nz" to "en",
        "us" to "en", "ca" to "en", "gb" to "en", "ie" to "en", "za" to "en",
        "my" to "en", "in" to "en",
        "mx" to "es", "ar" to "es", "cl" to "es", "co" to "es", "pe" to "es", "es" to "es",
        "br" to "pt", "pt" to "pt",
        "fr" to "fr", "de" to "de", "at" to "de", "ch" to "de",
        "it" to "it", "nl" to "nl", "be" to "nl",
        "se" to "sv", "no" to "no", "dk" to "da", "fi" to "fi",
        "ru" to "ru", "ua" to "uk", "pl" to "pl", "tr" to "tr",
        "eg" to "ar", "sa" to "ar", "ae" to "ar",
        "th" to "th", "il" to "he", "vn" to "vi",
    )

    /** 연도 -> (MM-DD -> 그 날짜에 걸린 이름들). 날짜 존재 여부 비교가 목적이라 이름은 set으로. */
    data class FetchResult(
        val byYear: Map<String, Map<String, Set<String>>>,
        val error: String?,
    )

    fun fetch(countryCode: String, langCode: String? = null): FetchResult {
        val lang = langCode ?: LANG_GUESS[countryCode]
        ?: return FetchResult(emptyMap(), "이 국가의 언어 코드 추정값이 없음 — 직접 지정 필요")
        val url = "https://calendars.icloud.com/holidays/${countryCode}_$lang.ics"
        return try {
            val request = HttpRequest.newBuilder(URI(url))
                .header("Accept-Encoding", "gzip")
                .timeout(Duration.ofSeconds(20))
                .GET()
                .build()
            val response = client.send(request, HttpResponse.BodyHandlers.ofByteArray())
            if (response.statusCode() != 200) {
                return FetchResult(emptyMap(), "HTTP ${response.statusCode()} ($url)")
            }
            val isGzip = response.headers().firstValue("Content-Encoding").orElse("") == "gzip"
            val bytes = if (isGzip) {
                GZIPInputStream(ByteArrayInputStream(response.body())).readBytes()
            } else {
                response.body()
            }
            FetchResult(parse(String(bytes, Charsets.UTF_8)), null)
        } catch (e: Exception) {
            FetchResult(emptyMap(), "요청 실패: ${e.message}")
        }
    }

    private val eventRegex = Regex("BEGIN:VEVENT(.*?)END:VEVENT", RegexOption.DOT_MATCHES_ALL)
    private val dateRegex = Regex("""DTSTART;VALUE=DATE:(\d{8})""")
    private val summaryRegex = Regex("""SUMMARY;LANGUAGE=[\w-]+:(.+)""")
    private val rruleRegex = Regex("""RRULE:FREQ=YEARLY;COUNT=(\d+)""")

    private fun parse(content: String): Map<String, Map<String, Set<String>>> {
        val result = mutableMapOf<String, MutableMap<String, MutableSet<String>>>()

        fun add(year: Int, mm: Int, dd: Int, name: String) {
            val mmdd = "%02d-%02d".format(mm, dd)
            result.getOrPut(year.toString()) { mutableMapOf() }
                .getOrPut(mmdd) { mutableSetOf() }
                .add(name)
        }

        for (match in eventRegex.findAll(content)) {
            val block = match.groupValues[1]
            val dateMatch = dateRegex.find(block) ?: continue
            val summaryMatch = summaryRegex.find(block) ?: continue
            val d = dateMatch.groupValues[1]
            val y0 = d.substring(0, 4).toInt()
            val mm = d.substring(4, 6).toInt()
            val dd = d.substring(6, 8).toInt()
            val name = summaryMatch.groupValues[1].trim()
            val count = rruleRegex.find(block)?.groupValues?.get(1)?.toIntOrNull() ?: 1
            for (i in 0 until count) {
                val y = y0 + i
                try {
                    LocalDate.of(y, mm, dd) // 유효성 검사(2/29 등)
                    add(y, mm, dd, name)
                } catch (e: DateTimeException) {
                    // 윤년 아닌 해의 2/29 등 — 건너뜀
                }
            }
        }
        return result
    }
}

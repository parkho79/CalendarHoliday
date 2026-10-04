import kotlinx.serialization.json.Json
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * 실제 데이터 생성 로직(Nager/Google fetch, holiday_corrections.json 적용)은 전부
 * update_holidays.py가 유일한 소스다. 이 도구는 그 로직을 Kotlin으로 다시 구현하지 않고,
 * 매번 서브프로세스로 그 스크립트를 직접 호출한다 — 두 군데에 비슷한 로직을 두면 시간이
 * 지나면서 서로 어긋나는 문제(이 저장소가 예전에 실제로 겪었던 문제)를 원천 차단하기 위함.
 */
object Pipeline {
    // tool/ 밑에서 실행되므로 한 단계 위가 CalendarHoliday 저장소 루트.
    val repoRoot: File = File(System.getProperty("user.dir")).let {
        if (it.name == "tool") it.parentFile else it
    }

    private val json = Json { ignoreUnknownKeys = true }

    /** stdout/stderr를 분리해서 받는다 — urllib3 등의 경고가 stderr로 나오는데, 합쳐버리면
     * JSON을 stdout에서 출력하는 호출(countryList 등)의 파싱이 깨진다. */
    data class ProcessResult(val success: Boolean, val stdout: String, val stderr: String)

    private fun runPython(vararg args: String): ProcessResult {
        return try {
            val process = ProcessBuilder(listOf("python3") + args)
                .directory(repoRoot)
                .start()
            val stdout = process.inputStream.bufferedReader().readText()
            val stderr = process.errorStream.bufferedReader().readText()
            val finished = process.waitFor(60, TimeUnit.SECONDS)
            if (!finished) {
                process.destroyForcibly()
                return ProcessResult(false, stdout, "$stderr\n(60초 넘게 응답 없어 강제 종료)")
            }
            ProcessResult(process.exitValue() == 0, stdout, stderr)
        } catch (e: Exception) {
            ProcessResult(false, "", "python3 실행 실패: ${e.message}")
        }
    }

    /** update_holidays.py에서 국가 목록을 직접 읽어온다 — Kotlin 쪽에 따로 하드코딩하지 않음. */
    fun countryList(): Result<CountryList> {
        val code = """
            import update_holidays as u, json
            print(json.dumps({'nager': list(u.NAGER_COUNTRIES.keys()), 'google': list(u.GOOGLE_ONLY_CALENDARS.keys())}))
        """.trimIndent()
        val result = runPython("-c", code)
        if (!result.success) return Result.failure(RuntimeException(result.stderr))
        return try {
            Result.success(json.decodeFromString(result.stdout.trim()))
        } catch (e: Exception) {
            Result.failure(RuntimeException("국가 목록 파싱 실패: stdout=${result.stdout} stderr=${result.stderr}"))
        }
    }

    /** 특정 국가만 재생성한다 (python3 update_holidays.py {code}). */
    fun regenerate(countryCode: String): Result<String> {
        val result = runPython("update_holidays.py", countryCode)
        return if (result.success) Result.success(result.stdout) else Result.failure(RuntimeException(result.stdout + "\n" + result.stderr))
    }

    fun readHolidayList(countryCode: String): Result<HolidayFile> {
        val file = File(repoRoot, "holiday_list_$countryCode.json")
        if (!file.exists()) return Result.failure(RuntimeException("파일 없음: ${file.name}"))
        return try {
            Result.success(json.decodeFromString(file.readText()))
        } catch (e: Exception) {
            Result.failure(RuntimeException("JSON 파싱 실패(${file.name}): ${e.message}"))
        }
    }
}

<div align="center">

# opus-like-fable

**Claude Opus를 Fable 5급 행동 프로파일로 구동하는 Claude Code 플러그인.**

![Claude Code plugin](https://img.shields.io/badge/Claude_Code-plugin-d97757)
![version](https://img.shields.io/badge/version-0.0.1-blue)
![license](https://img.shields.io/github/license/JunHyeongLee92/opus-like-fable)
![stars](https://img.shields.io/github/stars/JunHyeongLee92/opus-like-fable)

[English](README.md) · [한국어](README.ko.md)

</div>

Opus는 이미 유능합니다 — Fable이 *다르게 느껴지는* 건 행동 방식 때문입니다. 결론을
먼저 말하고, 묻는 대신 실행하고, 동의하는 대신 근거로 반박하고, 약속하는 대신
끝까지 해냅니다. 이 플러그인은 그 행동 레이어를 상시 스펙·런타임 hook·검증 루프로
Opus에 이식합니다.

## 설치

```sh
/plugin marketplace add JunHyeongLee92/opus-like-fable
/plugin install opus-like-fable@opus-like-fable
```

Opus 세션에서 쓰세요(`/model opus`). 이렇게 설치하면 세션이 바뀌어도 계속 켜져
있습니다. CLI도 됩니다: `claude plugin marketplace add …` 후 `claude plugin install …`.

## 사용법

설치하면 행동 스펙은 항상 켜져 있어 따로 호출할 게 없습니다. 작업을 맡겨 알맞은
접근을 알아서 고르게 하고 싶을 때(에이전트 fan-out, 검증, 코드베이스 훑기) 기억할
건 하나뿐입니다:

```sh
/fab 인증 모듈 리팩토링하고 깨진 데 없는지 검증해줘
```

진입점 하나 — 개별 스킬 이름을 외울 필요가 없습니다.

## 무엇이 바뀌나

| 일반적인 Opus | opus-like-fable 적용 |
|---|---|
| "당신 말이 전적으로 옳아요! 고칠게요." | 먼저 확인하고, 틀렸으면 근거로 반박 |
| "테스트 업데이트할까요?" | 그냥 업데이트; 위험·범위 변경만 묻는다 |
| "다음으로 X를 리팩토링하겠습니다"로 종료 | Stop hook이 턴을 막고 — 리팩토링이 지금 일어난다 |
| 질문 하나에 12개 파일을 읽음 | 탐색을 위임하고 결론 두 줄만 보유 |
| "이제 될 거예요!" (미검증) | 실행하고, 실패 포함 실제 결과 보고 |
| 작업 중 조용히 `git push` | 비가역 명령은 확인으로 승격 |

## 구성 요소

| 종류 | 이름 | 역할 |
|---|---|---|
| Spec | 6개 모듈 | 상시 행동 — communication, honesty, autonomy, delegation, reporting, memory |
| Hook | SessionStart | 스펙 주입(컴팩션 후에도 유지) |
| Hook | Stop | 미완성 작업으로 턴 종료 차단; 포맷/톤 린트 |
| Hook | UserPromptSubmit | 조건 발동형 리마인더 |
| Hook | PreToolUse | `git push`/`commit`, `rm -rf`, 패키지 publish 가드 |
| Skill | `/fab` | 알맞은 능력으로 라우팅하는 진입점 |
| Skill | `fable-orchestrate`, `fable-loop` | 멀티에이전트 fan-out; verify / judge / loop-until-dry |
| Agent | `fable-verifier`, `fable-judge`, `fable-explorer` | 반박형 검증, 루브릭 채점, 읽기 전용 탐색 |

<details>
<summary><strong>작동 원리</strong></summary>

세 개의 주입 채널이 Anthropic 자체 하네스가 행동을 입히는 방식 — 상시 스펙,
조건부 리마인더, 강제 집행 — 을 본떴습니다:

```
SessionStart  → 6개 모듈 스펙(~3k 토큰) 주입; 컴팩션 후 재주입
UserPromptSubmit → 직전 응답에 포맷/톤 위반 → 표적 리마인더;
                   아니면 12턴마다 압축 스펙
Stop          → 매 응답 린트; 마지막 문단이 일 대신 약속이면 턴 종료 차단
                (체인당 1회, 후속 제안은 면제)
PreToolUse    → git push/commit, publish, rm -rf, reset --hard → "ask"로 승격
                (조용히도, 강제 거부도 아니게 — 결정권은 당신에게)
```

</details>

<details>
<summary><strong>실제로 효과가 있나 (측정)</strong></summary>

블라인드 평가(`evals/`)가 baseline Opus와 Opus+스펙을 9개 행동 차원으로
채점했습니다(Opus 4.8):

- baseline이 미끄러지는 곳을 개선: **delegation +1.0**, **autonomy +0.5**,
  **formatting +0.33** (1–5 루브릭).
- 나머지 여섯 차원: Opus 4.8가 이미 5/5 — 플러그인은 유지할 뿐 없는 차이를
  만들지 않는다.
- formatting은 스펙 주입만으로는 가장 약한데, 이는 라이브 Stop-hook 린트가 잡는
  지점 — 스펙 복붙 대비 플러그인의 가치를 보여주는 가장 명확한 근거.

정직한 프레이밍: Opus 4.8은 이미 강하고, 가치는 넓게 퍼진 게 아니라 집중적입니다.
전체 정리: [`evals/findings-2way-baseline-harness.md`](evals/findings-2way-baseline-harness.md).

</details>

<details>
<summary><strong>이 플러그인이 아닌 것</strong></summary>

- 탈옥도 정체성 코스프레도 아님 — 모델은 자신을 Fable이라 주장하지 않으며, 모든
  가드는 위험한 행동에 *마찰을 더한다*.
- 능력 패치가 아님 — 상호작용 레이어를 겨냥하며, 체감의 대부분이 거기서 온다.

</details>

## 요구사항

bash, python3(표준 라이브러리만). hook 상태는 `/tmp`, 프로젝트 메모리는
`.claude/fable-memory/`에 저장됩니다.

## 라이선스 & 면책

MIT — [`LICENSE`](LICENSE) 참고. 비공식 커뮤니티 프로젝트이며 Anthropic과
제휴·보증 관계가 없습니다. "Claude", "Opus", "Fable", "Anthropic"은 Anthropic의
상표로 여기서는 지명적으로만 사용됩니다. Anthropic 소스나 시스템 프롬프트 텍스트를
포함하지 않으며, 행동 스펙은 공개적으로 관찰 가능한 행동 패턴을 다시 쓴 원본입니다.

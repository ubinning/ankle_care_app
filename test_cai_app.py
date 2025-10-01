import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="발목 상태 기록", page_icon="👣", layout="centered")

# 세션 초기화
if "user" not in st.session_state:
    st.session_state.user = None
if "records" not in st.session_state:
    st.session_state.records = {}   # 참여자별 기록 dict
if "page" not in st.session_state:
    st.session_state.page = "start"

# 한국 시간 (KST)
KST = datetime.timezone(datetime.timedelta(hours=9))
today = str(datetime.datetime.now(KST).date())

# ------------------- 시작 화면 -------------------
if st.session_state.page == "start":
    st.title("👣 발목 기록 앱")
    st.subheader("시작하려면 선택하세요")

    action = st.radio("동작 선택", ["회원가입", "로그인"])

    if action == "회원가입":
        new_user = st.text_input("새 아이디를 입력하세요")
        if st.button("회원가입"):
            if new_user.strip():
                if new_user in st.session_state.records:
                    st.error("⚠️ 이미 존재하는 아이디입니다. 다른 아이디를 사용하세요.")
                else:
                    st.session_state.records[new_user] = []
                    st.success("✅ 회원가입 완료! 이제 로그인하세요.")
            else:
                st.error("아이디를 입력해주세요.")

    elif action == "로그인":
        user = st.text_input("아이디를 입력하세요")
        if st.button("로그인"):
            if user.strip():
                if user in st.session_state.records:
                    st.session_state.user = user
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("⚠️ 등록되지 않은 아이디입니다. 먼저 회원가입을 해주세요.")
            else:
                st.error("아이디를 입력해주세요.")

# ------------------- 홈 화면 -------------------
elif st.session_state.page == "home":
    st.title(f"👋 환영합니다, {st.session_state.user} 님")
    st.write("최근 발목 상태를 확인하고 관리하세요!")

    if st.button("✍️ 오늘 발목 기록하기 / 수정하기"):
        st.session_state.page = "record"
        st.rerun()

    user_records = st.session_state.records[st.session_state.user]
    df = pd.DataFrame(user_records)

    if not df.empty:
        st.subheader("📊 최근 기록 요약")
        st.dataframe(df.tail(7))

        # 그래프 (최근 데이터 기준)
        st.line_chart(df.set_index("날짜")[["불안정감", "통증", "활동"]])

        # 경고 멘트
        recent = df.tail(7)
        avg_pain = recent["통증"].mean()
        incidents = (recent["삐끗여부"] == "있음").sum()
        if incidents >= 2:
            st.warning("⚠️ 최근 삐끗이 자주 발생했습니다. 발목 관리가 필요합니다!")
        elif avg_pain >= 6:
            st.warning("⚠️ 최근 통증이 심해지고 있어요. 전문가 상담이 필요할 수 있습니다.")
    else:
        st.info("아직 기록이 없습니다. 상단 버튼을 눌러 첫 기록을 남겨보세요!")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚪 로그아웃"):
            st.session_state.page = "start"
            st.session_state.user = None
            st.rerun()
    with col2:
        if st.button("❌ 계정 삭제"):
            del st.session_state.records[st.session_state.user]
            st.success("계정이 삭제되었습니다.")
            st.session_state.page = "start"
            st.session_state.user = None
            st.rerun()

# ------------------- 기록 화면 -------------------
elif st.session_state.page == "record":
    st.title("✍️ 오늘 발목 기록하기")

    user = st.session_state.user
    user_records = st.session_state.records[user]

    # 오늘 기록 확인
    existing_record = None
    for rec in user_records:
        if rec["날짜"] == today:
            existing_record = rec
            break

    with st.form("ankle_form"):
        condition = st.slider("오늘 발목 불안정감", 0, 10, existing_record["불안정감"] if existing_record else 5)
        pain = st.slider("오늘 통증 정도", 0, 10, existing_record["통증"] if existing_record else 3)
        activity = st.slider("오늘 활동 수준", 0, 10, existing_record["활동"] if existing_record else 5)

        incident = st.radio("오늘 삐끗/접질림 발생 여부",
                            ["없음", "있음"],
                            index=["없음", "있음"].index(existing_record["삐끗여부"]) if existing_record else 0)
        balance = st.radio("균형감/불안정감 인지",
                           ["없음", "있음"],
                           index=["없음", "있음"].index(existing_record["균형감"]) if existing_record else 0)

        with st.expander("더 자세히 기록할까요?"):
            management = st.multiselect(
                "🏥 오늘 한 관리",
                ["테이핑", "보호대", "냉찜질", "온찜질", "스트레칭", "마사지"],
                default=existing_record["관리"].split(", ") if existing_record and existing_record["관리"] else []
            )
            shoe = st.radio("👟 주로 신은 신발",
                            ["운동화", "구두", "슬리퍼", "맨발", "부츠"],
                            index=["운동화", "구두", "슬리퍼", "맨발", "부츠"].index(existing_record["신발"]) if existing_record else 0)
            surface = st.radio("🛤️ 주로 걸은 지면",
                               ["평지", "계단", "경사로", "울퉁불퉁", "미끄러움"],
                               index=["평지", "계단", "경사로", "울퉁불퉁", "미끄러움"].index(existing_record["지면"]) if existing_record else 0)

        submitted = st.form_submit_button("저장하기")
        if submitted:
            record = {
                "날짜": today,
                "불안정감": condition,
                "통증": pain,
                "활동": activity,
                "삐끗여부": incident,
                "균형감": balance,
                "관리": ", ".join(management),
                "신발": shoe,
                "지면": surface
            }
            if existing_record:
                # 수정: 오늘 기록 덮어쓰기
                user_records.remove(existing_record)
            user_records.append(record)
            st.success("오늘 기록이 저장/수정되었습니다 ✅")
            st.session_state.page = "home"
            st.rerun()

    if st.button("🏠 홈으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()

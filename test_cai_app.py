import streamlit as st
import pandas as pd
import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# 🔹 Firebase 초기화 (중복 방지)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

st.set_page_config(page_title="발목 상태 기록", page_icon="👣", layout="centered")

# 🔹 한국 시간
KST = datetime.timezone(datetime.timedelta(hours=9))
today = str(datetime.datetime.now(KST).date())

# 🔹 세션 초기화
if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "start"

# ------------------- 시작 화면 -------------------
if st.session_state.page == "start":
    st.title("👣 발목 기록 앱")

    action = st.radio("동작 선택", ["회원가입", "로그인"])

    if action == "회원가입":
        new_user = st.text_input("새 아이디를 입력하세요")
        if st.button("회원가입"):
            if new_user.strip():
                doc_ref = db.collection("users").document(new_user)
                if doc_ref.get().exists:
                    st.error("⚠️ 이미 존재하는 아이디입니다.")
                else:
                    doc_ref.set({"join_date": today})
                    st.success("✅ 회원가입 완료! 로그인하세요.")

    elif action == "로그인":
        user = st.text_input("아이디 입력")
        if st.button("로그인"):
            if user.strip():
                doc_ref = db.collection("users").document(user)
                if doc_ref.get().exists:
                    st.session_state.user = user
                    st.session_state.page = "home"
                    st.rerun()
                else:
                    st.error("⚠️ 등록되지 않은 아이디입니다. 회원가입을 먼저 해주세요.")

# ------------------- 홈 화면 -------------------
elif st.session_state.page == "home":
    st.title(f"👋 환영합니다, {st.session_state.user} 님")

    if st.button("✍️ 오늘 발목 기록하기 / 수정하기"):
        st.session_state.page = "record"
        st.rerun()

    # 🔹 Firestore에서 데이터 불러오기
    records = db.collection("ankle_records").where("user", "==", st.session_state.user).stream()
    data = [r.to_dict() for r in records]
    df = pd.DataFrame(data)

    if not df.empty:
        df = df.sort_values("date")
        st.subheader("📊 최근 기록 요약")
        st.dataframe(df.tail(7))

        st.line_chart(df.set_index("date")[["instability", "pain", "activity"]])

        # 🔹 고급 경고 분석
        recent = df.tail(7)
        avg_pain = recent["pain"].mean()
        incidents = (recent["sprain"] == "있음").sum()
        trend_increase = False
        if len(recent) >= 2 and recent["pain"].iloc[-1] - recent["pain"].iloc[0] >= 2:
            trend_increase = True

        if incidents >= 2:
            st.warning("⚠️ 최근 일주일 동안 발목 삐끗이 2회 이상 발생했습니다. 발목 안정화 운동과 휴식을 권장합니다.")
        elif avg_pain >= 6:
            st.warning("⚠️ 최근 평균 통증이 높습니다. 발목 사용을 줄이고 회복에 집중하세요.")
        elif trend_increase:
            st.warning("⚠️ 통증이 점점 증가하는 추세입니다. 과사용에 주의하세요.")
        else:
            st.info("💪 최근 발목 상태가 안정적입니다. 꾸준히 관리하세요!")
    else:
        st.info("아직 기록이 없습니다. 상단 버튼을 눌러 첫 기록을 남겨보세요!")

    # 🔹 건강 정보 섹션
    st.markdown("---")
    st.subheader("📚 발목 건강 정보")

    with st.expander("👟 발 모양에 따른 신발 추천"):
        st.info("✅ **평발**: 아치를 지지하는 신발 권장\n✅ **요족**: 충격 흡수가 좋은 쿠션 신발 권장\n✅ **정상 아치**: 일반 운동화 가능")

    with st.expander("❄️ 냉찜질 vs 온찜질"):
        st.info("❄️ **냉찜질**: 급성 손상, 부종·통증 감소에 효과적 (운동 직후)\n🔥 **온찜질**: 만성 통증, 근육 긴장 완화 (운동 전 준비)")

    with st.expander("🏥 적절한 발목 테이핑"):
        st.info("운동 전 안정성 확보, 운동 중 부상 예방, 운동 후 회복 보조.\n⚠️ 전문가 지도 또는 교육 영상 참고 후 실시 권장")

    if st.button("🚪 로그아웃"):
        st.session_state.page = "start"
        st.session_state.user = None
        st.rerun()

# ------------------- 기록 화면 -------------------
elif st.session_state.page == "record":
    st.title("✍️ 오늘 발목 기록하기")

    user = st.session_state.user
    doc_id = f"{user}_{today}"
    doc_ref = db.collection("ankle_records").document(doc_id)
    existing_record = doc_ref.get().to_dict()

    with st.form("ankle_form"):
        condition = st.slider("오늘 발목 불안정감", 0, 10, existing_record["instability"] if existing_record else 5)
        pain = st.slider("오늘 통증 정도", 0, 10, existing_record["pain"] if existing_record else 3)
        activity = st.slider("오늘 활동 수준", 0, 10, existing_record["activity"] if existing_record else 5)

        incident = st.radio("오늘 삐끗/접질림 발생 여부",
                            ["없음", "있음"],
                            index=["없음", "있음"].index(existing_record["sprain"]) if existing_record else 0)
        balance = st.radio("균형감/불안정감 인지",
                           ["없음", "있음"],
                           index=["없음", "있음"].index(existing_record["balance"]) if existing_record else 0)

        with st.expander("더 자세히 기록할까요?"):
            management = st.multiselect(
                "🏥 오늘 한 관리 (해당되는 항목 모두 선택)",
                ["테이핑", "보호대", "냉찜질", "온찜질", "스트레칭", "마사지"],
                default=existing_record["management"].split(", ") if existing_record and existing_record["management"] else []
            )
            shoe = st.radio("👟 주로 신은 신발",
                            ["운동화", "구두", "슬리퍼", "맨발", "부츠"],
                            index=["운동화", "구두", "슬리퍼", "맨발", "부츠"].index(existing_record["shoe"]) if existing_record else 0)
            surface = st.radio("🛤️ 주로 걸은 지면",
                               ["평지", "계단", "경사로", "울퉁불퉁", "미끄러움"],
                               index=["평지", "계단", "경사로", "울퉁불퉁", "미끄러움"].index(existing_record["surface"]) if existing_record else 0)

        submitted = st.form_submit_button("저장하기")
        if submitted:
            record = {
                "user": user,
                "date": today,
                "instability": condition,
                "pain": pain,
                "activity": activity,
                "sprain": incident,
                "balance": balance,
                "management": ", ".join(management),
                "shoe": shoe,
                "surface": surface
            }
            doc_ref.set(record)
            st.success("오늘 기록이 저장/수정되었습니다 ✅")
            st.session_state.page = "home"
            st.rerun()

    if st.button("🏠 홈으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()

import streamlit as st
from transcriber import Transcription
import docx
from datetime import datetime
import pathlib
import io
import matplotlib.colors as mcolors

# app wide config
st.set_page_config(
    page_title="SIGJ DOC",
    layout="wide",
    page_icon=""
)

# load stylesheet
with open('style.css') as f:
    st.markdown('<style>{}</style>'.format(f.read()),
                unsafe_allow_html=True)

# app sidebar for uplading audio files
with st.sidebar.form("input_form"):
    input_files = st.file_uploader(
        "ไฟล์บันทึก", type=["mp4", "m4a", "mp3", "wav"], accept_multiple_files=True)

    whisper_model = st.selectbox("ขนาดรูปแบบการถอดเสียง", options=[
        "tiny", "base", "small", "medium", "large"], index=4)

    pauses = st.checkbox("หยุดการถอดเสียง", value=False)

    transcribe = st.form_submit_button(label="Start")

if transcribe:
    if input_files:
        st.session_state.transcription = Transcription(
            input_files)
        st.session_state.transcription.transcribe(
            whisper_model
        )
    else:
        st.error("กรุณาเลือกไฟล์ตามที่กำหนด")

# if there is a transcription, render it. If not, display instructions
if "transcription" in st.session_state:

    for i, output in enumerate(st.session_state.transcription.output):
        doc = docx.Document()
        save_dir = str(pathlib.Path(__file__).parent.absolute()
                       ) + "/transcripts/"
        st.markdown(
            f"#### การถอดเสียงจากไฟล์ {output['name']}")
        st.markdown(
            f"_(whisper model:_`{whisper_model}` -  _language:_ `{output['language']}`)")
        color_coding = st.checkbox(
            "รหัสสีคำ", value=False, key={i}, help='การให้รหัสสีคำตามความเป็นไปได้ที่คำนั้นจะถูกจดจำอย่างถูกต้อง ระดับสีมีตั้งแต่สีเขียว (สูง) ถึงสีแดง (ต่ำ)')
        prev_word_end = -1
        text = ""
        html_text = ""
        # Define the color map
        colors = [(0.6, 0, 0), (1, 0.7, 0), (0, 0.6, 0)]
        cmap = mcolors.LinearSegmentedColormap.from_list('my_colormap', colors)

        with st.expander("การถอดเสียง"):
            for idx, segment in enumerate(output['segments']):
                for w in output['segments'][idx]['words']:
                    # check for pauses in speech longer than 3s
                    if pauses and prev_word_end != -1 and w['start'] - prev_word_end >= 3:
                        pause = w['start'] - prev_word_end
                        pause_int = int(pause)
                        html_text += f'{"."*pause_int}{{{pause_int}sek}}'
                        text += f'{"."*pause_int}{{{pause_int}sek}}'
                    prev_word_end = w['end']
                    if (color_coding):
                        rgba_color = cmap(w['probability'])
                        rgb_color = tuple(round(x * 255)
                                          for x in rgba_color[:3])
                        print(w['word'], w['probability'], rgb_color)
                    else:
                        rgb_color = (0, 0, 0)
                        print(w['word'], w['probability'], rgb_color)
                    html_text += f"<span style='color:rgb{rgb_color}'>{w['word']}</span>"
                    text += w['word']
                    # insert line break if there is a punctuation mark
                    if any(c in w['word'] for c in "!?.") and not any(c.isdigit() for c in w['word']):
                        html_text += "<br><br>"
                        text += '\n\n'
            st.markdown(html_text, unsafe_allow_html=True)
            doc.add_paragraph(text)

        # save transcript as docx. in local folder
        file_name = output['name'] + "-" + whisper_model + \
            "-" + datetime.today().strftime('%d-%m-%y') + ".docx"
        doc.save(save_dir + file_name)

        bio = io.BytesIO()
        doc.save(bio)
        st.download_button(
            label="Download การถอดเสียง",
            data=bio.getvalue(),
            file_name=file_name,
            mime="docx"
        )

else:
    # show instruction page
    st.markdown("<h1>Whisper AI บันทึกเสียงเป็นข้อความภาษาไทย</h1> <p> พัฒนาโดย Johanna Jaeger และ ผศ.นพ.กำธร ตันติวิทยาทันต์ ภายใต้ MIT License </p><h2 class='highlight'>คำแนะนำ: </h2> <ol><li>เลือกไฟล์ที่ต้องการถอดเสียง (สามารถทำได้หลายไฟล์)</li>" +
                "<li> เลือกแบบ (ขนาด Large เพื่อผลลัพธ์ที่ดีที่สุด) และพารามิเตอร์อื่นๆ แล้วคลิก 'Start'</li> <li> ตรวจสอบผลการถอดเสียงโดยเฉพาะการเว้นวรรค </li></ol>",
                unsafe_allow_html=True)

from flask import Flask, request, jsonify
from funasr import AutoModel
import numpy as np

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
# change the path to the exact path of the model
MODEL_PATH = "./models/paraformer-zh-streaming"

asr_model = None

chunk_size = [0, 10, 5]  # 600ms
encoder_chunk_look_back = 4
decoder_chunk_look_back = 1

@app.route("/transcribe", methods=["POST"])
def transcribe():
    try:
        audio_bytes = request.data
        #print(f"Received audio data: {len(audio_bytes)} bytes")
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        audio_float = np.ascontiguousarray(audio_data)
        
        chunk_stride = chunk_size[1] * 960  # 600ms
        total_chunk_num = int((len(audio_float)-1)/chunk_stride+1)
        chunk_text = ""
        cache = {}
        
        for i in range(total_chunk_num):
            start_idx = i * chunk_stride
            end_idx = min((i + 1) * chunk_stride, len(audio_float))
            speech_chunk = audio_float[start_idx:end_idx].copy()
            speech_chunk = np.ascontiguousarray(speech_chunk)
            
            is_final = i == total_chunk_num - 1
            res = asr_model.generate(
                input=speech_chunk,
                cache=cache,
                is_final=is_final,
                chunk_size=chunk_size,
                encoder_chunk_look_back=encoder_chunk_look_back,
                decoder_chunk_look_back=decoder_chunk_look_back
            )
            
            for t in res:
                if isinstance(t, dict) and "text" in t and len(t["text"].strip()):
                    chunk_text = chunk_text + ''.join(t["text"].strip())
        
        return jsonify({"text": chunk_text}), 200
        
    except Exception as e:
        print(f"Error in transcription: {str(e)}")
        return jsonify({"error": str(e)}), 500

def load_model():
    global asr_model
    print(f"Loading FunASR model from {MODEL_PATH}...")
    asr_model = AutoModel(
        model=MODEL_PATH,
        device="cpu",
        disable_pbar=True,
        disable_update=True
    )
    print("ASR Model loaded successfully.")

if __name__ == "__main__":
    load_model()
    app.run(host="0.0.0.0", port=5000)

from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from funasr import AutoModel
import numpy as np
import uvicorn
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import soundfile as sf
import tempfile
import traceback
import os
from datetime import datetime

MODEL_PATH = "./models/paraformer-zh"
MAX_REQUEST_SIZE = 8 * 1024 * 1024
asr_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Loading FunASR model from {MODEL_PATH}...")
    global asr_model
    asr_model = AutoModel(
        model=MODEL_PATH,
        device="cuda",
        model_type="paraformer",
        batch_size=1,
        disable_pbar=True,
        disable_update=True
    )
    print("ASR Model loaded successfully.")

    app.state.asr_model = asr_model

    # fastapi will take control
    yield

    print("Shutting down ASR model...")
    del app.state.asr_model

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

@app.post("/transcribe")
async def transcribe(request: Request):
    start_time = time.time()
    global asr_model
    if request.headers.get("content-length") and \
       int(request.headers["content-length"]) > MAX_REQUEST_SIZE:
        raise HTTPException(status_code=413, detail="Request too large")
    
    try:
        audio_bytes = await request.body()
        audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
        
        os.makedirs('./temp', exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        temp_wav_path = f'./temp/audio_{timestamp}.wav'

        sf.write(temp_wav_path, audio_data, 16000)

        result = asr_model.generate(
            input=temp_wav_path,
            batch_size=1,
            mode='online'
        )

        # 删除文件以清理
        # 暂时屏蔽删除逻辑，方便调试
        # if os.path.exists(temp_wav_path):
        #     os.remove(temp_wav_path)

        if isinstance(result, (list, tuple)):
            if len(result) > 0 and isinstance(result[0], dict):
                text = result[0].get('text', '')
            else:
                text = ' '.join([str(r) for r in result if r])
        else:
            text = str(result)
            
        elapsed_time = time.time() - start_time
        print(f"Server processing time: {elapsed_time:.3f} seconds")
        return {"text": text, "process_time": elapsed_time}
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        print(f"Error processing time: {elapsed_time:.3f} seconds")
        print(f"Exception: {e}")
        print(f"Stack trace:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "funasr_fastapi_server:app",
        host="0.0.0.0",
        port=5286,
        reload=False
    )

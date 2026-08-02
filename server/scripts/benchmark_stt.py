import os
import sys

server_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, server_dir)
sys.path.insert(0, os.path.join(server_dir, "rag"))

import jiwer
from gtts import gTTS
import tempfile
from pipeline.speech import transcribe_audio

# Synthetic Dataset: (ground_truth_text, spoken_text)
# We test DA-IICT specific jargon and general queries.
DATASET = [
    ("What is the fee structure for B.Tech ICT?", "What is the fee structure for B Tech I C T?"),
    ("Can I talk to Professor Subhas Chandra Nandy?", "Can I talk to Professor Subhas Chandra Nandy?"),
    ("Where is the CEP building located?", "Where is the C E P building located?"),
    ("When do admissions start for M.Des?", "When do admissions start for M Des?"),
    ("I need to speak with the Dean of Academic Affairs", "I need to speak with the Dean of Academic Affairs")
]

def generate_audio(text, output_path):
    tts = gTTS(text, lang='en')
    tts.save(output_path)

def run_benchmark():
    ground_truths = []
    predictions = []
    
    print("==================================================")
    print("Running STT Synthetic Benchmark with gTTS...")
    print("==================================================\n")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        for idx, (gt, spoken) in enumerate(DATASET):
            audio_path = os.path.join(tmpdir, f"sample_{idx}.mp3")
            generate_audio(spoken, audio_path)
            
            # Transcribe
            prediction = transcribe_audio(audio_path)
            
            # For jiwer, we generally lower everything and strip punctuation for a fair metric
            # but jiwer can also do this with its transform pipeline. 
            # We'll just pass the raw strings and let jiwer handle it via standard config.
            
            ground_truths.append(gt)
            predictions.append(prediction)
            
            print(f"Sample {idx+1}:")
            print(f"  Target Text : {gt}")
            print(f"  Whisper Out : {prediction}")
            print("-" * 50)
            
    # Calculate Word Error Rate using jiwer
    transformation = jiwer.Compose([
        jiwer.ToLowerCase(),
        jiwer.RemoveMultipleSpaces(),
        jiwer.RemovePunctuation(),
        jiwer.Strip()
    ])
    
    ground_truths = [transformation(gt) for gt in ground_truths]
    predictions = [transformation(pr) for pr in predictions]
    
    wer_score = jiwer.wer(ground_truths, predictions)
    cer_score = jiwer.cer(ground_truths, predictions)
    
    print("\n==================================================")
    print(f"Final Accuracy Metrics (Synthetic Dataset)")
    print("==================================================")
    print(f"Word Error Rate (WER)     : {wer_score:.2%}")
    print(f"Character Error Rate (CER): {cer_score:.2%}")
    
    # Accuracy is roughly 1 - Error Rate
    word_accuracy = max(0.0, 1.0 - wer_score)
    print(f"Estimated Word Accuracy   : {word_accuracy:.2%}")
    print("\nNote: These numbers are based on synthetic text-to-speech.")
    print("For real-world accuracy, evaluate against human voice recordings.")

if __name__ == "__main__":
    run_benchmark()

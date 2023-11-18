from six.moves import queue
import pyaudio
from google.cloud import speech
from django.shortcuts import render
from channels.generic.websocket import WebsocketConsumer
import json
import threading
import time
import random
import serial
from pydub import AudioSegment
from pydub.playback import play
from socket import socket, AF_INET, SOCK_DGRAM
from .serializer import UserInputSerializer
from pymagnitude import Magnitude


class SensorConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.start_publish()

    def disconnect(self, close_code):
        self.stop_publish()

    def start_publish(self):
        self.publishing = True
        self.t = threading.Thread(target=self.publish)
        self.t.start()

    def stop_publish(self):
        self.publishing = False
        self.t.join()

    def publish(self):
        # Serialの設定
        HOST = ''
        PORT = 4010

        s = socket(AF_INET, SOCK_DGRAM)
        s.bind((HOST, PORT))

        ser = serial.Serial('/dev/cu.usbmodem14101', 9600)
        not_used = ser.readline()

        exist_count = 0
        while True:
            if self.publishing == False:
                break
            val_arduino = ser.readline()
            val_decoded = val_arduino.decode()
            val_decoded = val_decoded.rstrip()
            print(val_decoded)
            if val_decoded == '1':
                exist_count += 1
            else:
                exist_count = 0

            if exist_count == 20:
                print(exist_count)
                print("++++++++++")
                self.publishing = False
                self.send(text_data=json.dumps([{'exist': val_decoded}]))

        ser.close()
        s.close()


class SensorLastConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.start_publish()

    def disconnect(self, close_code):
        self.stop_publish()

    def start_publish(self):
        self.publishing = True
        self.t = threading.Thread(target=self.publish)
        self.t.start()

    def stop_publish(self):
        self.publishing = False
        self.t.join()

    def publish(self):
        # Serialの設定
        HOST = ''
        PORT = 40011

        s = socket(AF_INET, SOCK_DGRAM)
        s.bind((HOST, PORT))

        ser = serial.Serial('/dev/cu.usbmodem14101', 9600)
        not_used = ser.readline()

        exist_count = 0
        while True:
            if self.publishing == False:
                break
            val_arduino = ser.readline()
            val_decoded = val_arduino.decode()
            val_decoded = val_decoded.rstrip()
            print(val_decoded)
            if val_decoded == '0':
                print(exist_count)
                exist_count += 1
            else:
                exist_count = 0

            if exist_count == 3000:
                # self.publishing = False
                self.send(text_data=json.dumps([{'exist': '0'}]))

        ser.close()
        s.close()


stream_close = False  # ストリーミング終了時にTrueとなる

STREAMING_LIMIT = 240000
SAMPLE_RATE = 16000
CHUNK_SIZE = int(SAMPLE_RATE / 10)


class ResumableMicrophoneStream:

    def __init__(self, rate, chunk_size):

        self._rate = rate
        self.chunk_size = chunk_size
        self._num_channels = 1

        # 取得した音声を格納するキュー
        self._buff = queue.Queue()

        # マイクから音声を入力するインスタンス
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=self._num_channels,
            rate=self._rate,
            input=True,
            frames_per_buffer=self.chunk_size,
            stream_callback=self._fill_buffer,
        )

    # with文実行時に呼ばれる
    def __enter__(self):

        global stream_close
        stream_close = False
        return self

    # with文終了時に呼ばれる
    def __exit__(self, type, value, traceback):

        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self._buff.put(None)
        self._audio_interface.terminate()
        global stream_close
        stream_close = True

    def _fill_buffer(self, in_data, *args, **kwargs):

        # マイクから入力した音声をキューに格納する
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self):

        global stream_close
        data_num = 0
        while not stream_close:
            data = []
            if len(data) == 0:
                print(data_num)
                data_num = data_num + 1
                if data_num == 200:
                    return

            chunk = self._buff.get()
            print(data)

            if chunk is None:
                return

            data.append(chunk)

            # キューが空になるまでdataリストに追加する
            while True:
                try:
                    chunk = self._buff.get(block=False)

                    if chunk is None:
                        return
                    data.append(chunk)

                except queue.Empty:
                    break

            yield b''.join(data)


## 音声のテキスト化を表示する関数
def listen_print_loop(responses, stream):

    global stream_close

    for response in responses:

        if not response.results:
            continue

        result = response.results[0]

        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        # 文末と判定したら区切る
        if result.is_final:
            print("========")
            print(transcript)
            print("========")
            # stream_close = True
            return transcript
        else:
            print('    ', transcript)

        # 終わりと言うと終了する
        if transcript == '終わり':
            # stream_close = True
            str(transcript).replace('終わり', '')
            return transcript


## Speech to Textを実行する関数
def excecute_speech_to_text_streaming():

    print('Start Speech to Text Streaming')

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=SAMPLE_RATE,
        language_code='ja-JP',
        max_alternatives=1)
    streaming_config = speech.StreamingRecognitionConfig(config=config,
                                                         interim_results=True)

    mic_manager = ResumableMicrophoneStream(SAMPLE_RATE, CHUNK_SIZE)
    with mic_manager as stream:

        # マイクから入力した音声の取得
        audio_generator = stream.generator()

        requests = (speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator)

        # Google Speech to Text APIを使って音声をテキストに変換
        responses = client.streaming_recognize(streaming_config, requests)

        # テキスト変換結果を表示する
        text = listen_print_loop(responses, stream)
        return text

    print('End Speech to Text Streaming')


class MicConsumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.start_publish()

    def disconnect(self, lose_code):
        self.stop_publish()

    def start_publish(self):
        self.publishing = True
        self.t = threading.Thread(target=self.publish)
        self.t.start()

    def stop_publish(self):
        self.publishing = False
        self.t.join()

    def publish(self):
        HOST = ''
        PORT = 4009

        s = socket(AF_INET, SOCK_DGRAM)
        s.bind((HOST, PORT))

        while True:
            if self.publishing == False:
                break

            # 体験者のデータを音声認識して保持
            voice = AudioSegment.from_file("static/sound/ai-voice/intro.wav",
                                           "wav")
            play(voice)
            voice = AudioSegment.from_file("static/sound/ai-voice/intro2.wav",
                                           "wav")
            play(voice)

            text = excecute_speech_to_text_streaming()

            print("====")
            print(text)
            print("====")
            if (text== None):
                print("===================")
                self.send(text_data=json.dumps([{
                'redirect_page': 1}]))
                self.publishing = False
                s.close()
                break

            positive_words = [
                'はい', 'うん', 'そう', 'そうだね', '住んでいる', '住んでる', 'Yes', 'はいはい'
            ]

            negative_words = [
                'いいえ', '違う', 'そうじゃない', '住んでいない', 'No', 'ノー', '住んで住んでない',
                'ではない', 'いない'
            ]

            is_citizen = 0
            if text in positive_words or 'はい' in text:
                print("pos")
                voice = AudioSegment.from_file(
                    "static/sound/ai-voice/answer1-1.wav", "wav")
                play(voice)
                is_citizen = 1
            elif text in negative_words or 'ない' in text:
                print("neg")
                print(text)
                voice = AudioSegment.from_file(
                    "static/sound/ai-voice/answer1-2.wav", "wav")
                play(voice)

            self.send(text_data=json.dumps([{
                'is_finished': 1,
            }]))
            self.publishing = False
            s.close()


class Mic2Consumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.start_publish()

    def disconnect(self, close_code):
        self.stop_publish()

    def start_publish(self):
        self.publishing = True
        self.t = threading.Thread(target=self.publish)
        self.t.start()

    def stop_publish(self):
        self.publishing = False
        self.t.join()

    def publish(self):
        HOST = ''
        PORT = 4013

        s = socket(AF_INET, SOCK_DGRAM)
        s.bind((HOST, PORT))

        while True:
            if self.publishing == False:
                break

            # 街らしさを教えてという質問を発話
            # 発話された音声をテキストにする
            time.sleep(2)
            voice = AudioSegment.from_file(
                "static/sound/ai-voice/question2.wav", "wav")
            play(voice)
            text = excecute_speech_to_text_streaming()

            print("====")
            print(text)
            print("====")
            if (text== None):
                print("===================")
                self.send(text_data=json.dumps([{
                'redirect_page': 1}]))
                self.publishing = False
                s.close()
                break

            # ページに表示するように設定
            self.send(text_data=json.dumps([{'text': text, 'q_num': '0'}]))

            # voice = AudioSegment.from_file("static/sound/ai-voice/wait.wav",
            #                                "wav")
            # play(voice)

            #  textと関連ワードを表示
            vectors = Magnitude('top/trained_models/chive-1.1-mc30.magnitude')
            similar_words = vectors.most_similar(text, topn=10)
            # フィルタリングする
            print(similar_words[0])
            print(similar_words[0][0])
            similar_word_list = []
            for v in similar_words:
                similar_word_list.append(v[0])
            similar_words = " ".join(similar_word_list)

            self.send(text_data=json.dumps([{
                'similar_words': similar_words,
                'q_num': '1'
            }]))

            # textから音声ファイルを生成して質問をする
            voice = AudioSegment.from_file(
                "static/sound/ai-voice/question2.5.wav", "wav")
            play(voice)

            text = excecute_speech_to_text_streaming()

            data = {'prompt': text, 'is_citizen': 0, 'place_category': 0}
            serializer = UserInputSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
            else:
                print(serializer.errors)

            self.send(text_data=json.dumps([{'text': text, 'q_num': '2'}]))
            self.publishing = False
            s.close()


class Mic3Consumer(WebsocketConsumer):

    def connect(self):
        self.accept()
        self.start_publish()

    def disconnect(self, close_code):
        self.stop_publish()

    def start_publish(self):
        self.publishing = True
        self.t = threading.Thread(target=self.publish)
        self.t.start()

    def stop_publish(self):
        self.publishing = False
        self.t.join()

    def publish(self):
        HOST = ''
        PORT = 4015

        s = socket(AF_INET, SOCK_DGRAM)
        s.bind((HOST, PORT))

        while True:
            if self.publishing == False:
                break

            # 質問をする
            voice = AudioSegment.from_file(
                "static/sound/ai-voice/question3.wav", "wav")
            play(voice)

            text = excecute_speech_to_text_streaming()
            print(text)

            positive_words = [
                'はい', 'うん', 'そう', 'そうだね', '住んでいる', '住んでる', 'Yes', 'はいはい'
            ]

            negative_words = [
                'いいえ', '違う', 'そうじゃない', '住んでいない', 'No', 'ノー', '住んで住んでない',
                'ではない', 'いない'
            ]

            is_finished = 0
            if text in positive_words or 'はい' in text:
                print("pos")
                print(text)
                voice = AudioSegment.from_file(
                    "static/sound/ai-voice/answer1.wav", "wav")
                play(voice)
                time.sleep(2)
                voice = AudioSegment.from_file(
                    "static/sound/ai-voice/graph.wav", "wav")
                play(voice)
                is_finished = 1
            elif text in negative_words or 'ない' in text:
                print("neg")
                print(text)
                voice = AudioSegment.from_file(
                    "static/sound/ai-voice/answer2.wav", "wav")
                play(voice)

            # ページに表示するように設定
            self.send(text_data=json.dumps([{'is_finished': is_finished}]))
            self.publishing = False
            s.close()

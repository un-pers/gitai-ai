from django.shortcuts import render
import serial
import time
import replicate
from googletrans import Translator
import os
from pymagnitude import Magnitude
from sklearn.manifold import TSNE
from pydub import AudioSegment
from pydub.playback import play
import json
import random
from .models import CityData, UserInput

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credential.json'
'''
[1ページ目]
未来感とエモいすみだのまちが入り混じったGenerativeな映像を流す
人がきたら、2ページ目に遷移

人感センサー -> arduino(0/1) -> python
'''


def top(request):
    '''
      Serial通信で1がきたらvoiceに遷移
      その他の場合はtop.htmlを表示
      '''

    # ページを変える
    return render(request, 'top.html')


'''
[2-1ページ目]
合図となる言葉を認識したら
街らしさの音声入力モードがスタート
入力されている時はLightついている

python -> arduino -> Light(ON/OFF)
一定時間以上、合図となる音声が入力されなかったら1ページ目に戻る
'''


def voice(request):
    # 合図となる掛け声がされたら
    # ページに表示する音声入力モードがスタート
    '''
  Web Socketで返事をもとに音声を変える
  '''
    return render(request, 'voice.html')


'''
[2-2ページ]
2つ目の質問をする。回答した内容をもとに近しい意味の
言葉を10個表示させる。
'''


def voice2(request):
    # 街らしさをきく
    '''
  Web Socketでtextを文末 or 入力終了時にリアルタイムでviewに送る
  '''
    return render(request, 'voice2.html')


'''
[3ページ目]
２ページ目で入力されたテキストをもとに既存のDBのテキストとのマッチング
マッチする文章がなかったら、SDのAPIで生成して映像と音声を表示

4ページ目に移動

'''


def result(request):
    '''
    入力された音声をもとにDBから類似度が高いテキストを検索
    閾値以上の映像が見つかったら、表示、見つからなかたらStable DiffusionのAPIで表示
    '''

    voice = AudioSegment.from_file("static/sound/ai-voice/generating.wav",
                                   "wav")
    play(voice)

    vectors = Magnitude('top/trained_models/chive-1.1-mc30.magnitude')
    # data_name = ['おばあちゃんと孫の会話','テレビ','掃除機','学童クラブの子供の声','工場','電話をしている人','八百屋','梅雨の時期のしとしとした雰囲気', '踏切']data_name = ['おばあちゃんと孫の会話','テレビ','掃除機','学童クラブの子供の声','工場','掃除機','電話をしている人','八百屋','梅雨の時期のしとしとした雰囲気', '踏切']
    data_name = ['おばあちゃんと孫の会話','定食屋のテレビ','金属をみつける町工場',
                 'コインランドリー','マンションの中庭','バイク屋さんの外','家から漏れる音',
                 '学童クラブの子供','金属を見つける町工場','風鈴の音',
                 '曇りの日の川','公園で喋るおじさん','クリーニング屋',
                 'お店の音','工事の音','新しい幼稚園','おしゃべりしながら自転車に乗る小学生',
                 'ザーザー音のなる精米機','ジャバジャバ水が出る井戸','たくさんの人が集まる車の店',
                 '街に生きる外国人','魚を買う近所のお母さん','公園で遊ぶ子どもたち','自転車に吠える犬',
                 '商店と配達するバイク','昔ながらの商店街','走る子ども','地域の喋るおばちゃん',
                 '木造密集している長屋','DIYのある路地','スカイツリー','たくさんの木材',
                 'ちょっとした路地','はみ出す緑','何気ない路地と自動販売機','街角の緑豊かな植栽',
                 '建物に挟まれた稲荷神社','古い掲示板','工場と緑','紙を扱う工場','重なる石と消火栓',
                 '歴史ある神社','老舗の魚屋さん']

    input_word = request.GET.get(key="text")
    print(input_word)
    print(vectors.most_similar(input_word, topn=10))
    similar_word = vectors.most_similar_to_given(input_word, data_name)
    print(similar_word)
    similarity = vectors.similarity(input_word, similar_word)
    print(similarity)

    similarity_threshould = 0.1
    sound_url2 = "static/sound/ai-voice/question3.wav"
    if similarity > similarity_threshould:
        img_url = '/static/img/' + similar_word + '.png'
        sound_url = '/static/sound/pre_data/' + similar_word + '.wav'
    else:
        img_url = generate_image(input_word)[0]
        sound_url = '/static/sound/neutral/マンホール.m4a'

    data = {
        'img_url': img_url,
        'sound_url': sound_url,
        'sound_url2': sound_url2,
        'input_word': input_word
    }
    return render(request, 'result.html', data)


def result2(request):
    return render(request, 'result2.html')


'''
画像生成システム
'''


def generate_image(prompt):
    REPLICATE_API_TOKEN = '066d292fe16f0c292830dd8fde02e492328c8010'
    model = replicate.models.get("stability-ai/stable-diffusion")
    # 英語に翻訳
    tr = Translator()
    result = tr.translate(prompt, src="ja", dest="en").text
    result = result + ',in Japan, digital art'
    imgs = model.predict(prompt=result, num_outputs=1)
    # 画像を取得
    img_urls = []
    for img_url in imgs:
        img_urls.append(img_url)
    return img_urls


'''
[裏ディスプレイ 1ページ目]
3ページ目で表示されたテキストを言語モデルのベクトルに変換、ベクトル化した既存のデータと一緒にグラフにして表示
'''


def graph(request):
    # 過去のテキストデータを一括で取得して2次元のベクトル化する
    # t-SNEで次元削減
    vectors = Magnitude('top/trained_models/chive-1.1-mc30.magnitude')
    tsne = TSNE(n_components=2, random_state=0, perplexity=30, n_iter=1000)

    # DBから街らしさのデータを取得
    data_name = ['おばあちゃんと孫の会話','定食屋のテレビ','金属をみつける町工場',
                 'コインランドリー','マンションの中庭','バイク屋さんの外','家から漏れる音',
                 '学童クラブの子供','金属を見つける町工場','風鈴の音',
                 '曇りの日の川','公園で喋るおじさん','クリーニング屋',
                 'お店の音','工事の音','新しい幼稚園','おしゃべりしながら自転車に乗る小学生',
                 'ザーザー音のなる精米機','ジャバジャバ水が出る井戸','たくさんの人が集まる車の店',
                 '街に生きる外国人','魚を買う近所のお母さん','公園で遊ぶ子どもたち','自転車に吠える犬',
                 '商店と配達するバイク','昔ながらの商店街','走る子ども','地域の喋るおばちゃん',
                 '木造密集している長屋','DIYのある路地','スカイツリー','たくさんの木材',
                 'ちょっとした路地','はみ出す緑','何気ない路地と自動販売機','街角の緑豊かな植栽',
                 '建物に挟まれた稲荷神社','古い掲示板','工場と緑','紙を扱う工場','重なる石と消火栓',
                 '歴史ある神社','老舗の魚屋さん']
    user_inputs = UserInput.objects.all()
    user_input = user_inputs[len(user_inputs) - 1].prompt
    print(user_input)
    data_name.append(user_input)

    #     user_input_list = []
    #     for v in user_inputs:
    #           user_input_list.append(v)

    data_size = []
    data_color = []
    for i in range(len(data_name)):
        n = random.randint(3, 30)
        data_size.append(n)
        n = random.randint(0, 1)
        if n == 0:
            data_color.append("#07BE06")
        else:
            data_color.append("#ffffff")

    name_emb_list = []
    name_emb_dict = {}
    for v in data_name:
        emb_vect = vectors.query(v)
        name_emb_list.append(emb_vect)

    name_tsne_emb_list = tsne.fit_transform(name_emb_list) + 400

    input_word = request.GET.get(key="text")
    # 強調するために番号を把握しておく
    data = {
        'data_name': data_name,
        'name_tsne_emb_list': name_tsne_emb_list.tolist(),
        'data_size': data_size,
        'data_color': data_color
    }
    return render(request, 'graph.html', {'data_json': json.dumps(data)})
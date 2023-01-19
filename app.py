from flask import Flask, session, render_template, request, jsonify

import requests
import certifi
ca = certifi.where()

from pymongo import MongoClient
client = MongoClient('mongodb+srv://test:sparta@cluster0.elmvpjv.mongodb.net/Cluster0?retryWrites=true&w=majority', tlsCAFile=ca)
db = client.dbsparta
app = Flask(__name__)
app.secret_key = "Mykey"

sessionId = 0

# API
# CONSTANT
REQ = {
    'KEY': 'User-Agent',
    'VALUE': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36',
}

###Sessions###
def checkSessionValidation():
  if session['id']:
    global sessionId;
    sessionId = session['id']
    return
  return render_template('/auth/login.html')


###HOME###
@app.route('/')
def home():
    if 'id' in session:
        global sessionId
        print(sessionId)
        return render_template('main.html')
    else:
        return render_template('/auth/login.html')

if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

###AUTH###
@app.route('/auth/login', methods=['GET'])
def getlogin():
    return render_template('/auth/login.html')


@app.route('/auth/login', methods=['POST'])
def logIn():
    user_id = request.form['inputId'].strip()
    user_pw = request.form['inputPw'].strip()
    error = True
    # 유효성 검사 (빈문자열, 4자리 미만, ID 존재여부 -> 존재하면 PW 일치 확인)
    if (len(user_id.strip()) == 0):
        msg = "ID를 입력해 주세요."
    elif (len(user_pw.strip()) == 0):
        msg = "PW를 입력해 주세요."
    elif (len(user_id) < 4 or len(user_pw) < 4):
        msg = "ID와 PW의 길이는 4자가 넘어야 합니다."
    elif (db.users.find_one({'id': user_id}) == None):  # 등록되지 않은 ID
        msg = "등록되지 않은 ID입니다. 회원가입 하세요."
    elif (db.users.find_one({'id': user_id})['pw'] != user_pw):  # ID, PW 일치 확인
        msg = "ID와 PW가 일치하지 않습니다. 다시 확인해보세요."
    else:
        msg = "로그인 성공"
        error = False  # 로그인 가능
        session['id'] = user_id
        global sessionId
        sessionId = user_id

    return jsonify({'message': msg, 'error': error})

@app.route('/auth/join', methods=['GET'])
def join():
    return render_template('/auth/join.html')

@app.route('/auth/signIn', methods=['POST'])
def signIn():
    inputId = request.form['inputId'].strip()
    inputPw = request.form['inputPw'].strip()
    inputName = request.form['inputName'].strip()
    error = True
    # 유효성 검사 (빈문자열, 4자리 미만, ID중복 여부)
    if (len(inputId.strip()) == 0):
        msg = "ID를 입력해 주세요."
    elif (len(inputPw.strip()) == 0):
        msg = "PW를 입력해 주세요."
    elif (len(inputId) < 4 or len(inputPw) < 4):
        msg = "ID와 PW의 길이는 4자가 넘어야 합니다."
    elif (db.users.find_one({'id': inputId}) != None):  # 이미 등록된 ID
        msg = "이미 등록된 ID라니까요."
    else:
        msg = "회원가입 완료!"
        error = False
        db.users.insert_one({'id': inputId, 'pw': inputPw, 'name': inputName})
    return jsonify({'message': msg, 'error': error})

@app.route('/auth/join/check', methods=['POST'])
def idCheck():
    inputId = request.form['inputId']
    error = True
    if (db.users.find_one({'id': inputId}) != None):
        msg = "중복된 ID입니다."
    else:
        msg = "가입이 가능한 ID입니다."
        error = False
    return jsonify({'message':msg, 'error':error})

#Logout
@app.route('/logout', methods=['GET'])
def logout():
    session.pop('id', None)
    return jsonify({'message': "로그아웃 하셨습니다."})

@app.route('/upload', methods=["GET"])
def upload():
    return render_template('/upload.html')

@app.route('/myPage')
def myPage():
    return render_template('/myPage.html')

###MAIN###
@app.route("/items", methods=["GET"])
def getItemList():
    allItems = list(db.items.find({}, {'_id': False}))
    unSelledItems = [x for x in allItems if x['status']==0]
    print(unSelledItems)
    return jsonify({'allItems': unSelledItems})


##Upload##
@app.route("/upload" , methods=["POST"]) ## 수정해야할사항 최대 입찰금액 -> 프론트에서 받기
def uploadItem():
    checkSessionValidation()
    itemList = list(db.items.find({}, {'_id': False}))
    itemNum = len(itemList) + 1
    title = request.form['title']
    image = request.files['pic']
    extension = image.filename.split('.')[-1]
    minBid = request.form['minBid']
    nowBid = request.form['nowBid']
    unitBid = request.form['unitBid']
    maxBid = request.form['maxBid']
    desc = request.form['desc']
    status = request.form['status']
    owner = sessionId
    if (minBid >= maxBid):
        return jsonify({'msg' : '낙찰가는 기본가보다 높아야 합니다.'})
    else:
        item = {
            'itemNum' : itemNum,
            'title' : title,
            'pic' : extension,
            'minBid' : int(minBid),
            'nowBid' : int(nowBid),
            'maxBid' : int(maxBid),
            'unitBid' : int(unitBid),
            'status' : int(status),
            'desc' : desc,
            'owner' : owner
        }
        db.items.insert_one(item)
        return jsonify({'msg' : '등록되었습니다.'})


###MyPage###
@app.route("/users", methods=["GET"])
def itemlist(): ##이 정보를 가지고 client에서 status에 따라 0 = 등록 중인 아이템, 1 = 낙찰된 아이템으로 나눠서 진행해주세요.
    return render_template('/myPage.html')

@app.route("/getId", methods=["GET"])
def getId(): ##이 정보를 가지고 client에서 status에 따라 0 = 등록 중인 아이템, 1 = 낙찰된 아이템으로 나눠서 진행해주세요.
    return jsonify({'id' : sessionId})

###Modify page###
@app.route('/detail', methods=["GET"])
def viewDetail():
    return render_template('/detail.html')
@app.route('/detail', methods=["POST"])
def bid():
    itemNum = request.form['itemNum']
    nowBid = request.form['nowBid']
    unitBid = request.form['unitBid']
    maxBid = request.form['maxBid']
    nowBid += unitBid
    id = sessionId
    if (nowBid >= maxBid):
        db.items.update_one({'name':itemNum},{'$set':{'nowBid':nowBid}})
        db.items.update_one({'name':itemNum},{'$set':{'owner': id}})
        return jsonify({'msg' : '낙찰되셨습니다!'})
    else:
        db.items.update_one({'name': itemNum}, {'$set': {'nowBid': nowBid}})
        return jsonify({'msg' : '입찰 완료!'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5001, debug=True)
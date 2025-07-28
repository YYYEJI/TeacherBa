from flask import Flask, request, jsonify
from flask_cors import CORS
from final import run_agent  # final.py에서 응답 생성 함수 가져오기

app = Flask(__name__)
CORS(app)  # CORS 허용 (프론트가 다른 포트일 경우)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_input = data.get("message", "")
    
    if not user_input:
        return jsonify({"response": "질문이 비어 있어요!"}), 400

    try:
        response = run_agent(user_input)
        if not response:
            return jsonify({"response": "답변을 생성하지 못했어요. 다시 질문해 주세요."})
        return jsonify({"response": response})
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({"response": f"오류 발생: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)

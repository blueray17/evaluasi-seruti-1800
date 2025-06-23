from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Mengizinkan permintaan dari domain lain

@app.route('/update-env', methods=['POST'])
def update_env():
    try:
        data = request.get_json(force=True)
        print("=== Data Diterima ===")
        print(f"CSRF_TOKEN: {data.get('CSRF_TOKEN')}")
        print(f"XSRF_TOKEN: {data.get('XSRF_TOKEN')}")
        print(f"COOKIES   : {data.get('COOKIES')}")
        print("=====================\n")

        return jsonify({
            "status": "success",
            "received": data
        }), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    print("Server berjalan di http://localhost:8001")
    app.run(port=8001, debug=True)

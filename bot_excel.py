import os
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8317063689:AAG_JX8j4QwwmeOQL8AerOTb1G-OhcDDJac"
user_status = {}
user_data = {}  # simpan data sementara per user

# ✅ /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_status[user_id] = "active"
    user_data[user_id] = []
    await update.message.reply_text(
        "👋 Halo! Kirim beberapa file .txt berisi data dengan format:\n"
        "`Nama Nomor Alias`\n\n"
        "Jika sudah selesai mengirim, ketik /proses untuk ubah ke Excel.\n"
        "Ketik /stop untuk menghentikan bot."
    )

# ✅ /stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_status[user_id] = "stopped"
    user_data[user_id] = []
    await update.message.reply_text("⏹ Bot dihentikan. Gunakan /start untuk memulai lagi.")

# ✅ Handle file TXT
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_status.get(user_id) == "stopped":
        await update.message.reply_text("⚠️ Bot sedang dihentikan. Gunakan /start untuk memulai lagi.")
        return

    file = await update.message.document.get_file()
    file_path = f"{user_id}_temp.txt"
    await file.download_to_drive(file_path)

    # Parsing file txt
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 2:
                nama = parts[0]
                nomor = parts[1]
                alias = " ".join(parts[2:]) if len(parts) > 2 else ""
                user_data[user_id].append([nama, nomor, alias])

    os.remove(file_path)
    await update.message.reply_text(f"📥 File diterima. Total data sementara: {len(user_data[user_id])}.")

# ✅ /proses
async def proses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_status.get(user_id) == "stopped":
        await update.message.reply_text("⚠️ Bot sedang dihentikan. Gunakan /start untuk memulai lagi.")
        return

    if not user_data.get(user_id):
        await update.message.reply_text("⚠️ Tidak ada data. Kirim file .txt dulu.")
        return

    data = user_data[user_id]
    total_data = len(data)
    total_files = (total_data + 24) // 25  # hitung jumlah file

    await update.message.reply_text(
        f"📊 Ditemukan {total_data} data.\n"
        f"📂 Akan dibagi menjadi {total_files} file Excel (max 25 data per file)."
    )
    await update.message.reply_text("⏳ Data sedang diproses, tunggu sebentar...")

    # Bagi data jadi potongan 25
    chunks = [data[i:i+25] for i in range(0, total_data, 25)]
    filenames = []
    for idx, chunk in enumerate(chunks, start=1):
        df = pd.DataFrame(chunk, columns=["姓名", "手机号", "别名"])
        out_file = f"data_{idx}.xlsx"
        df.to_excel(out_file, index=False)
        filenames.append(out_file)

    # Kirim file ke user
    for file in filenames:
        await update.message.reply_document(document=open(file, "rb"))

    await update.message.reply_text(f"✅ Proses selesai! Dibuat {len(filenames)} file Excel.")

    # Bersihkan data setelah diproses
    user_data[user_id] = []
    for file in filenames:
        os.remove(file)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("proses", proses))
    app.add_handler(MessageHandler(filters.Document.FileExtension("txt"), handle_file))
    print("🤖 Bot jalan...")
    app.run_polling()

if __name__ == "__main__":
    main()

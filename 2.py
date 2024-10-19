import streamlit as st  
import base64  
import io  
import os  
from google.oauth2.credentials import Credentials  
from google_auth_oauthlib.flow import Flow  
from googleapiclient.discovery import build  
from googleapiclient.http import MediaIoBaseUpload  
import anthropic  

# Thiết lập Claude API  
claude_api_key = "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"  
claude_client = anthropic.Anthropic(api_key=claude_api_key)  

# Xác định đường dẫn hiện tại  
current_dir = os.path.dirname(os.path.abspath(__file__))  

# Thiết lập Google Drive API  
SCOPES = ['https://www.googleapis.com/auth/drive.file']  
flow = Flow.from_client_secrets_file(  
    os.path.join(current_dir, 'client_secret_291966232305-uc5mei4d9ca9pdb6fbtsrpj9e1naod7g.apps.googleusercontent.com.json'),  
    scopes=SCOPES  
)  

# Dictionary để lưu trữ ảnh từ các tab  
tab_images = {  
    'Lâm sàng': [],  
    'Tiền căn': [],  
    'Công thức máu': [],  
    'Sinh hóa': [],  
    'Vi sinh': [],  
    'Chức năng HH': [],  
    'KMĐM': [],  
    'Điều trị': []  
}  

tab_name_mapping = {  
    'Lâm sàng': 'lam_sang',  
    'Tiền căn': 'tien_can',  
    'Công thức máu': 'cong_thuc_mau',  
    'Sinh hóa': 'sinh_hoa',  
    'Vi sinh': 'vi_sinh',  
    'Chức năng HH': 'chuc_nang_HH',  
    'KMĐM': 'kmdm',  
    'Điều trị': 'dieu_tri'  
}  

st.set_page_config(page_title="Ứng dụng Y tế", page_icon=":hospital:")  

st.title("Ứng dụng Y tế")  

# Tạo tabs  
tabs = st.tabs([  
    "Thông tin cơ bản", "Lâm sàng", "Tiền căn", "Công thức máu",  
    "Sinh hóa", "Vi sinh", "Chức năng HH", "KMĐM", "Điều trị"  
])  

# Tab Thông tin cơ bản  
with tabs[0]:  
    st.header("Thông tin cơ bản")  
    
    # Chụp ảnh mã số hồ sơ  
    image = st.camera_input("Chụp ảnh mã số hồ sơ")  
    
    if image:  
        # Chuyển đổi ảnh thành base64  
        image_base64 = base64.b64encode(image.getvalue()).decode('utf-8')  
        
        # Gửi ảnh đến Claude API để nhận dạng  
        response = claude_client.completion(  
            prompt=f"Hãy nhận dạng mã số hồ sơ trong ảnh sau:\n[IMAGE]{image_base64}[/IMAGE]",  
            model="claude-3-5-sonnet-20240620",  
            max_tokens_to_sample=300,  
        )  
        
        # Trích xuất mã số hồ sơ từ phản hồi của Claude  
        medical_record_number = response.completion.strip()  
        
        # Hiển thị và cho phép chỉnh sửa mã số hồ sơ  
        medical_record_number = st.text_input("Mã số hồ sơ", value=medical_record_number)  
    else:  
        medical_record_number = st.text_input("Mã số hồ sơ")  

# Tạo một khu vực chụp ảnh chung  
st.header("Chụp ảnh cho các mục")  
selected_tab = st.selectbox("Chọn mục để lưu ảnh", list(tab_images.keys()))  
captured_image = st.camera_input("Chụp ảnh", key="common_camera")  

if captured_image:  
    tab_images[selected_tab].append(captured_image)  
    st.success(f"Đã lưu ảnh vào mục {selected_tab}")  

# Hiển thị ảnh đã chụp trong mỗi tab  
for i, (tab_name, images) in enumerate(tab_images.items(), start=1):  
    with tabs[i]:  
        st.header(tab_name)  
        if images:  
            for idx, img in enumerate(images):  
                st.image(img, caption=f"Ảnh {idx+1}")  
        else:  
            st.write("Chưa có ảnh nào được chụp cho mục này.")  

# Nút để xóa tất cả ảnh  
if st.button("Xóa tất cả ảnh"):  
    for key in tab_images:  
        tab_images[key] = []  
    st.success("Đã xóa tất cả ảnh")  

# Nút để tải lên Google Drive  
if st.button("Tải lên Google Drive"):  
    creds = flow.run_local_server(port=0)  
    drive_service = build('drive', 'v3', credentials=creds)  
    
    # ID của thư mục cha trong Google Drive  
    parent_folder_id = "1z5rFTlISUyLY9QBoCTqz5O8ydaVCCgz5"  
    
    folder_name = f"Hồ sơ y tế - {medical_record_number}"  
    folder_metadata = {  
        'name': folder_name,  
        'mimeType': 'application/vnd.google-apps.folder',  
        'parents': [parent_folder_id]  
    }  
    
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()  
    folder_id = folder.get('id')  

    for tab_name, images in tab_images.items():  
        if images:  
            subfolder_metadata = {  
                'name': tab_name_mapping[tab_name],  
                'mimeType': 'application/vnd.google-apps.folder',  
                'parents': [folder_id]  
            }  
            subfolder = drive_service.files().create(body=subfolder_metadata, fields='id').execute()  
            subfolder_id = subfolder.get('id')  
            
            for idx, img in enumerate(images):  
                file_metadata = {  
                    'name': f'{tab_name_mapping[tab_name]}_{idx+1}.jpg',  
                    'parents': [subfolder_id]  
                }  
                media = MediaIoBaseUpload(io.BytesIO(img.getvalue()), mimetype='image/jpeg', resumable=True)  
                file = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()  

    st.success(f"Đã tải lên thành công hồ sơ {medical_record_number} lên Google Drive")
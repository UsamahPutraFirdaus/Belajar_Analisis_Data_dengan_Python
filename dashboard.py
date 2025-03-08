import streamlit as st 
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

url = "https://drive.google.com/file/d/1VIO4eiK8YoLp-2cCJx2i1MjkSw3jPWpM/view?usp=sharing"
file_id = url.split('/')[-2]
download_url = f'https://drive.google.com/uc?export=download&id={file_id}'
all_df = pd.read_csv(download_url)

# change type str/obj -> datetime
datetime_columns = ["order_approved_at"]
for column in datetime_columns:
    all_df[column] = pd.to_datetime(all_df[column])

def number_order_per_month(all_df, start_date, end_date):
    # Konversi start_date dan end_date ke pd.Timestamp
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)

    # Pastikan kolom order_approved_at dalam format datetime
    all_df["order_approved_at"] = pd.to_datetime(all_df["order_approved_at"], errors="coerce")

    # Jika rentang waktu yang dipilih tidak mencakup tahun 2017 sama sekali, kembalikan DataFrame dengan nilai 0 untuk semua bulan
    if (start_date.year > 2017) or (end_date.year < 2017):
        monthly_df = pd.DataFrame({
            "Month": ["January", "February", "March", "April", "May", "June", 
                      "July", "August", "September", "October", "November", "December"],
            "order_count": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        })
        return monthly_df

    # Filter data untuk tahun 2017
    filtered_df = all_df[(all_df["order_approved_at"] >= pd.to_datetime("2017-01-01")) & 
                         (all_df["order_approved_at"] <= pd.to_datetime("2017-12-31"))]

    # Filter data berdasarkan rentang waktu yang dipilih
    filtered_df = filtered_df[(filtered_df["order_approved_at"] >= start_date) & 
                              (filtered_df["order_approved_at"] <= end_date)]

    # Resample per bulan untuk menghitung jumlah pesanan
    monthly_df = filtered_df.resample(rule='M', on='order_approved_at').agg({
        "order_id": "count"  # Menghitung jumlah pesanan
    }).reset_index()

    # Ubah format tanggal menjadi hanya bulan untuk ditampilkan
    monthly_df["Month"] = monthly_df["order_approved_at"].dt.strftime('%B')
    monthly_df.rename(columns={"order_id": "order_count"}, inplace=True)

    # Mapping bulan ke angka agar bisa diurutkan dengan benar
    month_mapping = {
        "January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12
    }
    monthly_df["month_number"] = monthly_df["Month"].map(month_mapping)

    # Urutkan berdasarkan bulan
    monthly_df = monthly_df.sort_values("month_number").drop(columns=["month_number", "order_approved_at"])

    return monthly_df

def create_by_product_df(all_df):
    counts_product_name = all_df.groupby(by='product_category_name_english').product_id.count().sort_values(ascending=False).reset_index()
    return counts_product_name

def create_rfm(all_df):
    # Pastikan order_purchase_timestamp bertipe datetime
    all_df["order_purchase_timestamp"] = pd.to_datetime(all_df["order_purchase_timestamp"], errors="coerce")

    # Buat DataFrame untuk RFM Analysis
    rfm_df = all_df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",  # Tanggal order terakhir
        "order_id": "count",  # Jumlah order (Frequency)
        "price": "sum"  # Total pendapatan (Monetary)
    })

    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["max_order_timestamp"] = pd.to_datetime(rfm_df["max_order_timestamp"], errors="coerce").dt.date
    recent_date = all_df["order_purchase_timestamp"].dropna().max().date()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days if pd.notna(x) else None)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)

    rfm_data = rfm_df.copy()
    rfm_data["customer_id"] = range(1, len(rfm_data) + 1)

    return rfm_data


# ==================================================================================================
# ============================================ Side Bar ============================================
# ==================================================================================================

with st.sidebar:
    st.image('https://github.com/UsamahPutraFirdaus/Belajar_Analisis_Data_dengan_Python/blob/main/shop.jpg?raw=true')

    min_date = pd.to_datetime(all_df["order_approved_at"]).min()
    max_date = pd.to_datetime(all_df["order_approved_at"]).max()

    start_date, end_date = st.date_input(
        label="Rentang Waktu",
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
    st.write('Copyright (C) © 2025 by Usamah')


# ==================================================================================================
# ============================================= Header =============================================
# ==================================================================================================

st.header('E-Commerce Public Dataset')

# ==================================================================================================
# ========================================== Trend Orders ==========================================
# ==================================================================================================
daily_orders_df = number_order_per_month(all_df, start_date, end_date)

st.subheader('Monthly Orders (2017)')
st.subheader('Filter Only Works in the 2017 Year Range')

# Plot data
fig, ax = plt.subplots(figsize=(15, 6))

ax.plot(
    daily_orders_df["Month"],
    daily_orders_df["order_count"],
    marker='o', 
    linewidth=2,
    color="#72BCD4"
)

ax.set_title("Number of Orders per Month (2017)", loc="center", fontsize=20)
ax.set_xlabel("Month", fontsize=12)
ax.set_ylabel("Order Count", fontsize=12)
ax.tick_params(axis='x', labelsize=10, rotation=45)  # Rotasi agar lebih mudah dibaca
ax.tick_params(axis='y', labelsize=10)

# Tambahkan nilai di atas titik-titik pada grafik
for i, txt in enumerate(daily_orders_df["order_count"]):
    ax.text(
        i, txt, f'{txt}', ha='center', va='bottom',
        fontsize=10, fontweight='bold'
    )

# Tampilkan plot di Streamlit
st.pyplot(fig)

# ==================================================================================================
# ====================================== Best & Worst Product ======================================
# ==================================================================================================
best_worst_products_df=create_by_product_df(all_df)


st.subheader("Best & Worst Product")
col1, col2 = st.columns(2)

with col1:
    highest_product_sold=best_worst_products_df['product_id'].max()
    st.markdown(f"Higest Number : **{highest_product_sold}**")

with col2:
    lowest_product_sold=best_worst_products_df['product_id'].min()
    st.markdown(f"Lowest Number : **{lowest_product_sold}**")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(12, 6))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

sns.barplot(x='product_id', y='product_category_name_english', data= best_worst_products_df.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title('Produk Terlaris', loc='center', fontsize= 18)
ax[0].tick_params(axis= 'y', labelsize =15)

for i, value in enumerate(best_worst_products_df.head(5)['product_id']):
    ax[0].text(value, i, f'{value}', ha='center', va='center', fontsize =12, color= 'black')


sns.barplot(x='product_id', y='product_category_name_english', data=best_worst_products_df.sort_values(by='product_id', ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position('right')
ax[1].yaxis.tick_right()
ax[1].set_title('Produk Terendah', loc='center', fontsize=18)
ax[1].tick_params(axis='y', labelsize=15)

for i, value in enumerate(best_worst_products_df.sort_values(by='product_id', ascending=True).head(5)['product_id']):
    ax[1].text(value, i, f'{value}', ha='center', va= 'center', fontsize= 12, color= 'black')

plt.suptitle('Best & Worst Perform Product', fontsize = 20)
st.pyplot(fig)

# ==================================================================================================
# ========================================== RFM Analysis ==========================================
# ==================================================================================================
rfm=create_rfm(all_df)

st.subheader("RFM Analysis")

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

tab1, tab2, tab3 = st.tabs(["Recency", "Frequency", "Monetary"])

with tab1:
    data_recency = rfm.sort_values(by='recency', ascending=True).head(5)

    fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
    
    sns.barplot(y='recency', x='customer_id', data=data_recency, palette=colors, ax=ax)
    ax.set_ylabel("Recency (Days)")
    ax.set_xlabel("Customer ID")
    ax.set_title("By Recency (Days)", fontsize=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, fontsize=12)

    for p in ax.patches:
        ax.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=12, color='black')

    st.pyplot(fig)

with tab2:
    data_frequency = rfm.sort_values(by="frequency", ascending=False).head(5)
    
    fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
    
    sns.barplot(y="frequency", x="customer_id", data=data_frequency, palette=colors, ax=ax)
    ax.set_ylabel("Frequency")
    ax.set_xlabel("Customer ID")
    ax.set_title("By Frequency", fontsize=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, fontsize=12)

    for p in ax.patches:
        ax.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=12, color='black')

    st.pyplot(fig)

with tab3:
    data_monetary = rfm.sort_values(by="monetary", ascending=False).head(5)
    
    fig, ax = plt.subplots(figsize=(8, 4), dpi=200)
    
    sns.barplot(y="monetary", x="customer_id", data=data_monetary, palette=colors, ax=ax)
    ax.set_ylabel("Monetary Value")
    ax.set_xlabel("Customer ID")
    ax.set_title("By Monetary", fontsize=15)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=30, fontsize=12)

    for p in ax.patches:
        ax.annotate(f"{p.get_height():.0f}", (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=12, color='black')

    st.pyplot(fig)
    

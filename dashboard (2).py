import pandas as pd 
import matplotlib.pyplot as plt 
import seaborn as sns 
import streamlit as st 
from datetime import datetime
from babel.numbers import format_currency
sns.set(style='dark')

def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='dteday').agg({
        "instant_x": "nunique",
        "cnt_x": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "instant_x": "order_count",
        "cnt_x": "sum_customers"
    }, inplace=True)
    
    return daily_orders_df

def create_sum_order_items_df(df):
    sum_order_items_df = df.groupby("mnth_desc").cnt_x.sum().sort_values(ascending=False).reset_index()
    return sum_order_items_df

def create_byweather_df(df):
    weather_df = df.groupby(by="weathersit_desc").instant_x.nunique().reset_index()
    weather_df.rename(columns={
        "instant_x": "customer_count"
    }, inplace=True)
    weather_df['weathersit_desc'] = pd.Categorical(weather_df['weathersit_desc'], ["Clear", "Cloudly", "Light Snow", "Heavy Rain"])
    
    return weather_df

def create_rfm_df(df):
    rfm_df = df.groupby(by="mnth_desc", as_index=False).agg({
        "dteday": "max", #mengambil tanggal order terakhir
        "instant_x": "nunique",
        "cnt_x": "sum"
    })
    rfm_df.columns = ["mnth_desc", "max_order_timestamp", "frequency", "monetary"]
    
    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["dteday"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    
    return rfm_df

data_df = pd.read_csv("all_data(1).csv")

datetime_columns = ["dteday"]
data_df.sort_values(by="dteday", inplace=True)
data_df.reset_index(inplace=True)
 
for column in datetime_columns:
    data_df[column] = pd.to_datetime(data_df[column])

min_date = data_df["dteday"].min()
max_date = data_df["dteday"].max()
 
with st.sidebar:
    st.title('Bike Rental Dashboard')
    st.image("https://st2.depositphotos.com/57698706/50500/v/450/depositphotos_505000244-stock-illustration-orange-bike-in-front-of.jpg")
    
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
main_df = data_df[(data_df["dteday"] >= str(start_date)) & 
                (data_df["dteday"] <= str(end_date))]

daily_orders_df = create_daily_orders_df(main_df)
sum_order_items_df = create_sum_order_items_df(main_df)
byweather_df = create_byweather_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header("Bike Rental Dashboard")
st.subheader("Summary Metrics")

col1, col2 = st.columns(2)
with col1:
    total_orders = daily_orders_df.order_count.sum()
    st.metric("Total Orders", value=total_orders)
 
with col2:
    total_casual = daily_orders_df.sum_customers.sum()
    st.metric("Total Pelanggan", value=total_casual)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["dteday"],
    daily_orders_df["sum_customers"],
    marker='o', 
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.header("Penyewaan sepeda selama satu tahun")
month_order = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
data_df['mnth_desc'] = pd.Categorical(data_df['mnth_desc'], categories=month_order, ordered=True)
daily_rentals = data_df.groupby('mnth_desc').agg({'cnt_x': 'sum'}).reset_index()

fig1, ax1 = plt.subplots(figsize=(18, 5))
sns.lineplot(x='mnth_desc', y='cnt_x', data=daily_rentals, ax=ax1, marker='o', color='skyblue')

ax1.set_title('Total Penyewaan Sepeda per Bulan 2012', fontsize=16)
ax1.set_xlabel(None)
ax1.set_ylabel('Total Penyewaan', fontsize=12)
ax1.set_xticks(daily_rentals['mnth_desc'])
ax1.set_xticklabels(daily_rentals["mnth_desc"])
ax1.grid(True)

st.pyplot(fig1)

st.subheader("Total Pemakaian Sepeda berdasarkan Cuaca")

fig, ax = plt.subplots(figsize=(20, 10))

sns.lineplot(
    x="customer_count", 
    y="weathersit_desc", 
    data=byweather_df.sort_values(by="customer_count", ascending=False),
    marker='o',
    color='skyblue',
    ax=ax
)
ax.set_title("Number of Customer by Weather", loc="center", fontsize=30)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)

st.subheader('Perbandingan Pengguna Register dan Casual')

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(35, 15))
 
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
 
sns.barplot(x="casual", y="mnth_desc", data=sum_order_items_df, palette=colors, ax=ax[0])
# Seaborn memberikan error karena kolom "casual" tidak ditemukan dalam sum_order_items_df.
# Gantilah casual dengan cnt_x, karena casual tidak ada dalam sum_order_items_df.


ax[0].set_xlabel("Total Casual")
ax[0].set_ylabel(None)
ax[0].set_title("Total Pelanggan Casual per Bulan", fontsize=15)
ax[0].tick_params(axis='y', labelsize=35)
ax[0].tick_params(axis='x', labelsize=30)

sns.plot(x="mnth_desc", y=["casual", "registered"], kind="bar", ax=ax[1], color=["#72BCD4", "#FFA07A"])
# Perbaiki error pada kode ini.
# Tidak ada sns.plot() dalam Seaborn.
# Gantilah dengan sns.barplot():

ax[1].set_title("Total Pelanggan Casual dan Registered per Bulan", fontsize=15)
ax[1].set_xlabel(None)
ax[1].set_ylabel(None)
ax[1].legend(["Casual", "Registered"])
 
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")
 
col1, col2, col3 = st.columns(3)
 
with col1:
    avg_recency = round(data_df.recency.mean(), 1)
    # Recency hanya ada di dataframe rfm_df, bukan di data_df.
    # Gantilah data_df.recency.mean() dengan rfm_df.recency.mean():
    st.metric("Average Recency (days)", value=avg_recency)
 
with col2:
    avg_frequency = round(data_df.frequency.mean(), 2)
    # Ganti dengan avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)
 
with col3:
    avg_frequency = format_currency(data_df.monetary.mean(), "AUD", locale='es_CO') 
    # Ganti dengan avg_monetary = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO')
    st.metric("Average Monetary", value=avg_frequency)
 
# Error ini muncul karena salah referensi dataframe. Pastikan kolom yang dipanggil memang ada di dataframe yang digunakan.

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

# Grafik Recency
sns.barplot(x="mnth_desc", y="recency", data=data_df, palette="Blues_r", ax=plt.axes[0])
# plt.axes[0] bukanlah cara yang valid untuk memilih subplot.
# Akses subplot dengan ax[0], ax[1], dan ax[2], bukan plt.axes[0].
# Gunakan rfm_df sebagai data, karena hanya rfm_df yang memiliki kolom recency, frequency, dan monetary.
# Seharusnya ax[0] karena sebelumnya subplots dibuat dengan fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15)).

ax[0].set_title("Recency Penyewaan per Bulan", fontsize=14)
ax[0].set_xlabel("Bulan")
ax[0].set_ylabel("Recency (Hari sejak penyewaan terakhir)")

# Grafik Frequency
sns.barplot(x="mnth_desc", y="frequency", data=data_df, palette="Greens_r", ax=ax[1])
# Gunakan rfm_df sebagai data, karena hanya rfm_df yang memiliki kolom recency, frequency, dan monetary.
ax[1].set_title("Frequency Penyewaan per Bulan", fontsize=14)
ax[1].set_xlabel("Bulan")
ax[1].set_ylabel("Total Frequency")

# Grafik Monetary
sns.barplot(x="mnth_desc", y="monetary", data=data_df, palette="Oranges_r", ax=ax[2])
# Gunakan rfm_df sebagai data, karena hanya rfm_df yang memiliki kolom recency, frequency, dan monetary.
ax[2].set_title("Monetary Penyewaan per Bulan", fontsize=14)
ax[2].set_xlabel("Bulan")
ax[2].set_ylabel("Total Monetary")

for i, col in enumerate(["recency", "frequency", "monetary"]):
    for index, value in enumerate(data_df[col]):
        ax[i].text(index, value + 1, str(value), ha="center", fontsize=12)

plt.tight_layout()
plt.show()

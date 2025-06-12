import matplotlib.pyplot as plt
import geopandas as gpd
import contextily as ctx
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, blue
from reportlab.pdfbase import pdfmetrics # สำหรับลงทะเบียนฟอนต์
from reportlab.pdfbase.ttfonts import TTFont # สำหรับลงทะเบียนฟอนต์ TrueType
import os
import tempfile

# --- ส่วนที่ 1: ลงทะเบียนฟอนต์ THSarabunNew สำหรับ ReportLab ---
# ตรวจสอบให้แน่ใจว่าไฟล์ฟอนต์เหล่านี้อยู่ในโฟลเดอร์เดียวกับสคริปต์ของคุณ
# หรือระบุพาธแบบเต็มไปยังไฟล์ฟอนต์
FONT_DIR = "." # ถ้าฟอนต์อยู่ในโฟลเดอร์เดียวกับสคริปต์
# หรือระบุพาธแบบเต็ม: FONT_DIR = "C:/Users/YourUser/Fonts"

try:
    pdfmetrics.registerFont(TTFont('THSarabunNew', os.path.join(FONT_DIR, 'THSarabunNew.ttf')))
    pdfmetrics.registerFont(TTFont('THSarabunNew-Bold', os.path.join(FONT_DIR, 'THSarabunNew Bold.ttf')))
    pdfmetrics.registerFont(TTFont('THSarabunNew-Italic', os.path.join(FONT_DIR, 'THSarabunNew Italic.ttf')))
    pdfmetrics.registerFont(TTFont('THSarabunNew-BoldItalic', os.path.join(FONT_DIR, 'THSarabunNew BoldItalic.ttf')))

    pdfmetrics.registerFontFamily('THSarabunNew',
                                  normal='THSarabunNew',
                                  bold='THSarabunNew-Bold',
                                  italic='THSarabunNew-Italic',
                                  boldItalic='THSarabunNew-BoldItalic')
    print("SUCCESS: THSarabunNew fonts registered with ReportLab.")
except Exception as e:
    print(f"ERROR: Could not register THSarabunNew fonts. Make sure font files are in '{FONT_DIR}' and accessible. Error: {e}")

# --- สิ้นสุดส่วนลงทะเบียนฟอนต์ ---


def generate_static_map_image_to_file(shp_filepath, output_size_inches=(8, 6)):
    """
    Generates a static map image based on the extent of a given shapefile
    and saves it to a temporary file, ensuring the aspect ratio is maintained.
    """
    try:
        gdf = gpd.read_file(shp_filepath)
        print(f"Loaded shapefile: {shp_filepath} with CRS: {gdf.crs}")
    except Exception as e:
        print(f"ERROR: Could not load shapefile '{shp_filepath}': {e}")
        return None

    gdf_to_plot = gdf
    print(f"Using GeoDataFrame with original CRS: {gdf_to_plot.crs}")

    fig, ax = plt.subplots(figsize=output_size_inches, dpi=300)

    gdf_to_plot.plot(ax=ax, color="red", markersize=10, alpha=0.7, zorder=2)
    print("Data plotted on map.")

    try:
        ctx.add_basemap(ax, crs=gdf_to_plot.crs.to_string(), source=ctx.providers.OpenStreetMap.Mapnik)
        print("SUCCESS: Basemap added to plot using gdf extent and original CRS.")
    except Exception as e:
        print(f"ERROR: Failed to add basemap (check internet or provider or CRS): {e}")
        ax.set_title(f"Map Load Failed\n({str(e).splitlines()[0]})")
        ax.set_facecolor('lightgray')
        
    ax.set_aspect('equal', adjustable='box') 
    
    ax.set_axis_off()
    plt.tight_layout(pad=0) 

    temp_file = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            temp_file = tmp.name
            plt.savefig(temp_file, format='png', bbox_inches='tight', pad_inches=0) 
            print(f"DEBUG: Map saved to temporary file: {temp_file}.")
    except Exception as e:
        print(f"ERROR: Failed to save map image to temporary file: {e}")
        temp_file = None
    finally:
        plt.close(fig)

    return temp_file

def create_custom_report_template_with_generated_map(
    filename="report_template_generated_map.pdf",
    pm25_shp_filepath="pm25.shp"
):
    page_width, page_height = portrait(A4)
    c = canvas.Canvas(filename, pagesize=portrait(A4))

    margin = 0.5 * inch
    usable_width = page_width - (2 * margin)
    usable_height = page_height - (2 * margin)

    # --- ส่วนที่ 1: แผนที่ (2/3 ของหน้ากระดาษ) ---
    map_display_width = usable_width * (2/3)
    map_display_height = usable_height
    map_x = margin
    map_y = margin

    print(f"DEBUG: Map display area: x={map_x}, y={map_y}, width={map_display_width}, height={map_display_height}")

    map_output_size_inches = (map_display_width / inch, map_display_height / inch)
    print(f"DEBUG: Matplotlib figsize will be: {map_output_size_inches[0]:.2f}x{map_output_size_inches[1]:.2f} inches")

    temp_map_filepath = generate_static_map_image_to_file(
        shp_filepath=pm25_shp_filepath,
        output_size_inches=map_output_size_inches
    )

    if temp_map_filepath and os.path.exists(temp_map_filepath):
        try:
            c.drawImage(temp_map_filepath, map_x, map_y, 
                        width=map_display_width, height=map_display_height,
                        preserveAspectRatio=True) 
            print(f"SUCCESS: Map image loaded from '{temp_map_filepath}' and drawn in PDF.")
        except Exception as e:
            print(f"ERROR: Could not draw map image in PDF (ReportLab error): {e}")
            c.setFont("Helvetica-Bold", 16)
            c.setFillColor(black)
            c.drawString(map_x + 50, map_y + map_display_height / 2, "Map Drawing Error")
            c.drawString(map_x + 50, map_y + map_display_height / 2 - 20, f"Error: {e}")
        finally:
            try:
                os.remove(temp_map_filepath)
                print(f"DEBUG: Removed temporary map file: {temp_map_filepath}")
            except Exception as e:
                print(f"WARNING: Could not remove temporary file '{temp_map_filepath}': {e}")
    else:
        print("ERROR: Temporary map file was not created or not found. Map not available.")
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(black)
        c.drawString(map_x + 50, map_y + map_display_height / 2, "Map Not Available")
        c.drawString(map_x + 50, map_y + map_display_height / 2 - 20, "Check console for map generation errors.")

    # Add a title for the map section (ใช้ฟอนต์ THSarabunNew-Bold)
    # ควรใช้ฟอนต์ THSarabunNew-Bold สำหรับหัวข้อ
    c.setFont("THSarabunNew-Bold", 14) # <-- ใช้ฟอนต์ THSarabunNew-Bold
    # c.drawString(map_x + 10, map_y + map_display_height - 30, "แผนที่ PM2.5 (2/3 ของหน้ากระดาษ)")


    # --- ส่วนที่ 2: คำบรรยาย (1/3 ด้านข้างขวา - ส่วนบน) ---
    description_width = usable_width * (1/3)
    description_x = map_x + map_display_width + margin / 2
    description_height = usable_height * (3/4)
    description_y = usable_height - description_height + margin

    # ใช้ฟอนต์ THSarabunNew-Bold สำหรับหัวข้อคำบรรยาย
    c.setFont("THSarabunNew-Bold", 16) # <-- ใช้ฟอนต์ THSarabunNew-Bold
    c.setFillColor(blue)
    c.drawString(description_x + 10, description_y + description_height - 30, "รายละเอียด / คำบรรยาย")

    # ใช้ฟอนต์ THSarabunNew สำหรับเนื้อหาคำบรรยาย
    c.setFont("THSarabunNew", 10) # <-- ใช้ฟอนต์ THSarabunNew
    c.setFillColor(black)
    description_text = [
        "ข้อมูลเกี่ยวกับคุณภาพอากาศ PM2.5 ในพื้นที่ที่แสดงบนแผนที่.",
        "จุดสีแดงบนแผนที่แสดงตำแหน่งและค่า PM2.5.",
        "ข้อมูลนี้มีความสำคัญต่อการประเมินสุขภาพและสิ่งแวดล้อม.",
        "",
        "คำแนะนำ: ควรตรวจสอบค่า PM2.5 อย่างสม่ำเสมอ",
        "โดยเฉพาะในช่วงที่มีมลพิษสูง และควรป้องกันตนเอง.",
        "",
        "สามารถนำข้อมูลไปใช้ในการวางแผนและตัดสินใจเพื่อ",
        "ปรับปรุงคุณภาพอากาศในระยะยาว."
    ]
    textobject = c.beginText(description_x + 10, description_y + description_height - 50)
    # ใช้ฟอนต์ THSarabunNew สำหรับ textobject
    textobject.setFont("THSarabunNew", 10) # <-- ใช้ฟอนต์ THSarabunNew
    textobject.setFillColor(black)
    for line in description_text:
        textobject.textLine(line)
    c.drawText(textobject)


    # --- ส่วนที่ 3: เครดิตผู้จัดทำ (1/3 ด้านข้างขวา - ส่วนล่าง) ---
    credit_width = usable_width * (1/3)
    credit_x = description_x
    credit_height = usable_height * (1/4)
    credit_y = margin

    # ใช้ฟอนต์ THSarabunNew-Bold สำหรับหัวข้อเครดิต
    c.setFont("THSarabunNew-Bold", 12) # <-- ใช้ฟอนต์ THSarabunNew-Bold
    c.setFillColor(black)
    c.drawString(credit_x + 10, credit_y + credit_height - 30, "ผู้จัดทำ:")
    
    # ใช้ฟอนต์ THSarabunNew สำหรับเนื้อหาเครดิต
    c.setFont("THSarabunNew", 10) # <-- ใช้ฟอนต์ THSarabunNew
    c.drawString(credit_x + 10, credit_y + credit_height - 50, "ชื่อ-นามสกุล: คุณเจมินี่ AI")
    c.drawString(credit_x + 10, credit_y + credit_height - 65, "ตำแหน่ง: ผู้ช่วยอัจฉริยะ")
    c.drawString(credit_x + 10, credit_y + credit_height - 80, "วันที่: 12 มิถุนายน 2568") # วันที่ปัจจุบัน

    c.save()
    print(f"สร้างไฟล์ '{filename}' เรียบร้อยแล้ว")

if __name__ == "__main__":
    create_custom_report_template_with_generated_map(pm25_shp_filepath="pm25.shp")
import os
import ezdxf
import zipfile
import tempfile
import streamlit as st


def remove_and_replace_block(dxf_path, output_path, block_name, template_dxf_path):
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()
        removed_count = 0

        for entity in list(msp.query('INSERT')):
            if entity.dxf.name == block_name:
                msp.delete_entity(entity)
                removed_count += 1

        template_doc = ezdxf.readfile(template_dxf_path)

        if block_name in doc.blocks:
            del doc.blocks[block_name]

        if block_name in template_doc.blocks:
            new_block = template_doc.blocks[block_name]
            new_block_def = doc.blocks.new(name=new_block.name)
            for entity in new_block:
                new_block_def.add_entity(entity.copy())
            msp.add_blockref(block_name, (0, 0))

        doc.saveas(output_path)
        return True, removed_count
    except Exception as e:
        return False, str(e)


def main():
    st.title("DXF Block Replace Tool")
    st.markdown("Upload a ZIP of DXF files and a template DXF file to replace a block.")

    block_name = st.text_input("Block Name to Replace")
    template_file = st.file_uploader("Upload Template DXF", type=["dxf"])
    zip_file = st.file_uploader("Upload ZIP of DXF Files", type=["zip"])

    if st.button("Process"):
        if not block_name or not template_file or not zip_file:
            st.warning("Please provide all required inputs.")
            return

        with st.spinner("Processing..."):
            with tempfile.TemporaryDirectory() as temp_dir:
                template_path = os.path.join(temp_dir, "template.dxf")
                with open(template_path, "wb") as f:
                    f.write(template_file.read())

                zip_path = os.path.join(temp_dir, "input.zip")
                with open(zip_path, "wb") as f:
                    f.write(zip_file.read())

                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)

                dxf_files = [f for f in os.listdir(temp_dir) if f.lower().endswith(".dxf")]
                out_dir = os.path.join(temp_dir, "updated")
                os.makedirs(out_dir, exist_ok=True)

                success_count = 0
                for fname in dxf_files:
                    input_path = os.path.join(temp_dir, fname)
                    output_path = os.path.join(out_dir, fname)
                    success, result = remove_and_replace_block(input_path, output_path, block_name, template_path)
                    if success:
                        success_count += 1
                    else:
                        st.error(f"Failed on {fname}: {result}")

                # Package output files
                out_zip_path = os.path.join(temp_dir, "updated_dxf.zip")
                with zipfile.ZipFile(out_zip_path, "w") as zipf:
                    for f in os.listdir(out_dir):
                        zipf.write(os.path.join(out_dir, f), arcname=f)

                with open(out_zip_path, "rb") as f:
                    st.success(f"Processed {success_count} file(s) successfully.")
                    st.download_button("Download Updated DXFs", f, file_name="updated_dxf.zip")

if __name__ == "__main__":
    main()

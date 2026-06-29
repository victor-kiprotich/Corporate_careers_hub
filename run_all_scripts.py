import os
import subprocess
import sys

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Get the directory where this script is located
base_dir = os.path.dirname(os.path.abspath(__file__))

# List of all Python files found
python_files = [
    "Accor/accor.py",
    "AcdiVoca/acdi.py",
    "AfricanUnion/au.py",
    "AgaKhan/aga.py",
    "Air/air.py",
    "Airtel/airtel.py",
    "Amazon/amazon.py",
    "BAT/bat.py",
    "BCG/bcg.py",
    "Capital/capi.py",
    "Carrefour/carre.py",
    "Clinton/clint.py",
    "Conservation/cons.py",
    "EIDU/eidu.py",
    "ERM/erm.py",
    "G4S/g4s.py",
    "GardaWorld/garda.py",
    "Glovo/glovo.py",
    "Google/google.py",
    "Heineken/hein.py",
    "IEBC/iebc.py",
    "IWG/iwg.py",
    "Irvine/ivr.py",
    "Jumia/jumia.py",
    "KOKO/koko.py",
    "KPC/kpc.py",
    "KPLC/kplc.py",
    "KenGen/kengen.py",
    "KenyaAirways/kpa.py",
    "Lesaffre/les.py",
    "Lewis/lewis.py",
    "LivingGoods/living.py",
    "MIDIS/mid.py",
    "Mckinsey/mck.py",
    "Microsoft/microsoft.py",
    "MillarCameron/milar.py",
    "NCBA/ncba.py",
    "NTT_DATA/ntt.py",
    "Natmedia/nat.py",
    "NeumannKaffee/kaffee.py",
    "NovaPioneer/nova.py",
    "Prospect33/prospect.py",
    "QONA/qona.py",
    "Reckitt/reckitt.py",
    "RoyalMedia/royal.py",
    "SAP/sap.py",
    "SIC/sic.py",
    "SNV/snv.py",
    "Seaways/sea.py",
    "Solidaridad/soli.py",
    "SunKing/sun.py",
    "TouchInspiration/touch.py",
    "UNFPA/unfpa.py",
    "absa/absa.py",
    "cloverleaf/clover.py",
    "deloitte/deloitte.py",
    "dlight/dlight.py",
    "equity/equity.py",
    "i&m-/i&m.py",
    "jotun/jotun.py",
    "kcb/kcb.py",
    "kq/kq.py",
    "kra/kra.py",
    "mastercard/master.py",
    "mkopa/mkopa.py",
    "oneacre/one.py",
    "rentokil/rento.py",
    "safaricom/safscraping.py",
    "sightsavers/sight.py",
    "standardAero/aero.py",
    "sunculture/sunc.py",
    "tala/tala.py",
    "undp/undp.py"
]

print("=" * 80)
print("RUNNING ALL PYTHON SCRIPTS")
print("=" * 80)

working_scripts = []
failed_scripts = []
error_details = {}

for script_path in python_files:
    full_path = os.path.join(base_dir, script_path)
    
    # Check if file exists
    if not os.path.exists(full_path):
        print(f"\n❌ NOT FOUND: {script_path}")
        failed_scripts.append(script_path)
        error_details[script_path] = "File not found"
        continue
    
    print(f"\n🔍 Running: {script_path}")
    print("-" * 80)
    
    try:
        # Run the script with UTF-8 env vars to prevent emoji printing UnicodeEncodeErrors on Windows
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        
        result = subprocess.run(
            [sys.executable, full_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
            cwd=os.path.dirname(full_path),
            env=env
        )
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {script_path}")
            if result.stdout:
                print(f"Output:\n{result.stdout}")
            working_scripts.append(script_path)
        else:
            print(f"❌ FAILED: {script_path}")
            if result.stderr:
                print(f"Error:\n{result.stderr}")
            failed_scripts.append(script_path)
            error_details[script_path] = result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏱️ TIMEOUT: {script_path}")
        failed_scripts.append(script_path)
        error_details[script_path] = "Script timed out"
    except Exception as e:
        print(f"❌ ERROR: {script_path} - {str(e)}")
        failed_scripts.append(script_path)
        error_details[script_path] = str(e)

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\n✅ Working scripts ({len(working_scripts)}):")
for script in working_scripts:
    print(f"  - {script}")

print(f"\n❌ Failed scripts ({len(failed_scripts)}):")
for script in failed_scripts:
    print(f"  - {script}")

if error_details:
    print("\n" + "=" * 80)
    print("ERROR DETAILS")
    print("=" * 80)
    for script, error in error_details.items():
        print(f"\n{script}:")
        print(f"  {error}")

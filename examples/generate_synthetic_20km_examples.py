from __future__ import annotations
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from ucd.calculations.first_design import apply_load_calculation
from ucd.calculations.cable_library import merge_builtin_catalogs, apply_catalog_record
from ucd.calculations.project_application import apply_catalog_candidate_to_project
from ucd.calculations.cable_template_generator import build_generic_cable
from ucd.calculations.installation_coupling import project_with_synchronized_installation_geometry
from ucd.models.project import (
    DesignProgressData,
    BondingConnection,
    BondingLinkBox,
    BondingMinorSection,
    BondingNode,
    ProjectData,
    ProjectSourceAuditData,
    RouteSection,
    SourceConflictRecord,
    SourceValueRecord,
    default_bonding_system,
    default_installation_design,
    thermal_design_from_route_sections,
)

EX = ROOT / 'examples'
from synthetic_catalog_factory import merge_synthetic_catalogs


def build_synthetic_bonding(total_length_m: float = 20_000.0, section_count: int = 21):
    """Create seven complete cross-bonding groups with transportable cable sections.

    Twenty-one equal minor sections keep every cut below the illustrative 1 km
    drum limit after joint/termination tails and installation allowance.
    """
    total = float(total_length_m)
    count = max(3, int(section_count))
    step = total / count
    bonding = default_bonding_system(total)
    nodes = [BondingNode('T1', 'Sentetik başlangıç terminasyonu', 0.0, 'TERMINATION', 0.20, True)]
    for index in range(1, count):
        pos = step * index
        nodes.append(BondingNode(f'J{index:03d}', f'Sentetik ek noktası {index:02d}', pos, 'SECTIONALIZING_JOINT', 0.0, False))
    nodes.append(BondingNode('T2', 'Sentetik bitiş terminasyonu', total, 'TERMINATION', 0.20, True))

    boxes = []
    connections = []
    for index in range(1, count):
        node_id = f'J{index:03d}'
        box_id = f'LB{index:03d}'
        pos = step * index
        major_boundary = index % 3 == 0
        for node in nodes:
            if node.node_id == node_id:
                node.grounded = major_boundary
                break
        boxes.append(BondingLinkBox(
            box_id,
            f"Sentetik {'grounding' if major_boundary else 'cross-bonding'} link box {index:02d}",
            node_id,
            pos,
            3.0,
            'COAXIAL',
            not major_boundary,
            True,
        ))
        if major_boundary:
            connections.extend([
                BondingConnection(box_id, node_id, 'A', 'G', 'SOLID_GROUND'),
                BondingConnection(box_id, node_id, 'B', 'G', 'SOLID_GROUND'),
                BondingConnection(box_id, node_id, 'C', 'G', 'SOLID_GROUND'),
            ])
        else:
            connections.extend([
                BondingConnection(box_id, node_id, 'A', 'B', 'CROSS'),
                BondingConnection(box_id, node_id, 'B', 'C', 'CROSS'),
                BondingConnection(box_id, node_id, 'C', 'A', 'CROSS'),
            ])

    phase_orders = ('ABC', 'BCA', 'CAB')
    sections = []
    for index in range(1, count + 1):
        start_id = 'T1' if index == 1 else f'J{index - 1:03d}'
        end_id = 'T2' if index == count else f'J{index:03d}'
        start = step * (index - 1)
        end = total if index == count else step * index
        sections.append(BondingMinorSection(
            f'MS{index:03d}',
            f'Sentetik minör kesim {index:02d}',
            start_id,
            end_id,
            end - start,
            phase_orders[(index - 1) % 3],
            f'CH {start:.1f}-{end:.1f} m',
            (index - 1) // 3 + 1,
        ))
    bonding.nodes = nodes
    bonding.link_boxes = boxes
    bonding.minor_sections = sections
    bonding.connections = connections
    return bonding


def build_base() -> ProjectData:
    p=ProjectData(
        project_name='Sentetik 20 km Çift Devre Yeraltı Kablo Hattı',
        project_code='DITUS-DEMO-20KM',
        description=(
            'Tamamen sentetik, herhangi bir gerçek tesis veya müşteriyi temsil etmeyen '
            '20 km yeraltı kablo tasarım örneği. Eğitim, arayüz denetimi ve regresyon içindir.'
        ),
        created_at='2026-01-01T00:00:00',
        modified_at='2026-01-01T00:00:00',
    )
    b=p.design_basis
    b.system_voltage_kv=34.5
    b.frequency_hz=50.0
    b.circuit_count=2
    b.active_circuit_count=2
    b.n_minus_one_enabled=True
    b.apparent_power_mva=20.0
    b.active_power_mw=19.0
    b.power_factor=0.95
    b.future_growth_percent=5.0
    b.design_margin_percent=10.0
    b.total_route_length_m=20_000.0
    b.installation_profile='DIRECT_BURIED_TREFOIL'
    b.burial_depth_m=1.20
    b.phase_spacing_m=0.060
    b.circuit_spacing_m=0.80
    b.soil_thermal_resistivity_km_w=1.20
    b.soil_thermal_value_source='SYNTHETIC_DESIGN_INPUT'
    apply_load_calculation(b)

    p.design_progress=DesignProgressData(
        system_load='COMPLETE', route='PRELIMINARY', cable='PRELIMINARY',
        thermal='NOT_RUN', bonding='NOT_RUN', fault_epr='NOT_RUN', svl='NOT_RUN',
        final_design='NOT_READY', maturity_level='L2_IEC60287_ROUTE',
        missing_data=['Üretici onaylı kablo yapısı', 'Saha termal özdirenç ölçümü'],
    )
    # Fiziksel katmanları üretici verisi içermeyen 40,5 kV parametrik jenerik
    # şablondan başlat; proje kablosu yine açıkça sentetik ve koşulludur.
    p.cable = build_generic_cable(
        record_id='SYN-BASE-MV40K5-AL400-35',
        profile_id='MV40K5',
        material='Al',
        area_mm2=400.0,
        screen_area_mm2=35.0,
        screen_profile='CWS',
        stranding='COMPACT_ROUND',
    )
    p.cable.name='Sentetik 35 kV XLPE Tek Damarlı Kablo'
    p.cable.manufacturer=''
    p.cable.series=''
    p.cable.model=''
    p.cable.catalog_record_id=''
    p.cable.snapshot_id=''
    p.cable.snapshot_hash=''
    p.cable.snapshot_created_at=''
    p.cable.data_status='DRAFT'
    p.cable.voltage_kv=34.5
    p.cable.voltage_class='20.3/35 (40.5) kV'
    p.cable.frequency_hz=50.0
    p.cable.design_current_a=b.design_current_per_circuit_a
    p.cable.arrangement='Trefoil'
    p.cable.validation_notes=[
        'Sentetik örnektir; gerçek proje, saha veya üretici uygunluk kanıtı değildir.',
        'Nihai tasarımda tüm kablo ve aksesuar verileri üretici dokümanlarıyla değiştirilmelidir.',
    ]

    p.route_sections=[
        RouteSection(
            'RS-01 Sentetik standart hendek', 12_000.0, 'Standart hendek', 1.40, 1.20,
            'CS-SYN-01', 25.0, phase_spacing_m=0.060, backfill_thermal_resistivity_km_w=1.0, backfill_effective_radius_m=0.25,
            notes='Sentetik ana güzergâh bölümü.', start_chainage_m=0.0, end_chainage_m=12_000.0,
        ),
        RouteSection(
            'RS-02 Sentetik yüksek termal özdirenç bölgesi', 3_000.0, 'Standart hendek', 1.50, 1.80,
            'CS-SYN-02', 28.0, phase_spacing_m=0.060, backfill_thermal_resistivity_km_w=1.0, backfill_effective_radius_m=0.25,
            notes='Sentetik kritik termal bölge.', start_chainage_m=12_000.0, end_chainage_m=15_000.0,
        ),
        RouteSection(
            'RS-03 Sentetik yol geçişi duct bank', 1_000.0, 'Beton kanal', 1.60, 1.50,
            'CS-SYN-03', 27.0, phase_spacing_m=0.060, backfill_thermal_resistivity_km_w=1.0, backfill_effective_radius_m=0.25,
            notes='Sentetik duct bank geçişi.', start_chainage_m=15_000.0, end_chainage_m=16_000.0,
        ),
        RouteSection(
            'RS-04 Sentetik HDD geçişi', 4_000.0, 'HDD', 5.50, 1.60,
            'CS-SYN-04', 25.0, phase_spacing_m=0.060, backfill_thermal_resistivity_km_w=1.0, backfill_effective_radius_m=0.25,
            notes='Sentetik HDD kesimi.', start_chainage_m=16_000.0, end_chainage_m=20_000.0,
        ),
    ]
    p.thermal_design=thermal_design_from_route_sections(p.route_sections)
    p.thermal_design.route_length_m=20_000.0
    for i, region in enumerate(p.thermal_design.regions, start=1):
        region.name=f'Sentetik termal bölge {i}'
        region.source_reference='SYNTHETIC_DESIGN_INPUT'
    p.bonding=build_synthetic_bonding(20_000.0, 21)
    p.bonding.phase_spacing_m=0.060
    p.bonding.circuit_spacing_m=0.80
    p.procurement.waste_percent=0.5
    p.installation_design=default_installation_design(p.cable,p.design_basis,p.thermal_design)
    for i, section in enumerate(p.installation_design.cross_sections, start=1):
        section.name=f'Sentetik fiziksel kesit {i}'
        section.source_reference='SYNTHETIC_DESIGN_INPUT'
        section.data_state='DRAFT'
        section.notes='Tamamen sentetik 20 km örnek hat kesiti.'
        # burial_depth_m is the shallowest cable axis.  Keep the full trefoil
        # envelope and bottom cover inside the excavation in the critical zone.
        if 'TR-02' in section.region_ids:
            section.channel_geometry.trench_depth_m = max(
                section.channel_geometry.trench_depth_m, 1.75
            )
    merge_builtin_catalogs(p.cable_library)
    merge_synthetic_catalogs(p.cable_library)
    p.source_audit=ProjectSourceAuditData(
        source_name='DiTuS sentetik örnek veri üreticisi',
        source_file='',
        scope='UNDERGROUND_ONLY',
        records=[], conflicts=[], missing_required_data=[],
        notes='Harici proje dosyasından veya gerçek tesisten veri içermez.',
    )
    p.cad_source=''
    return project_with_synchronized_installation_geometry(p)

base=build_base()
(EX/'synthetic_20km_line.ucd.json').write_text(json.dumps(base.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')

audit=deepcopy(base)
audit.project_name='Sentetik 20 km Kaynak Denetimi Örneği'
audit.project_code='DITUS-DEMO-20KM-AUDIT'
audit.source_audit=ProjectSourceAuditData(
    source_name='DiTuS sentetik kaynak denetimi girdileri',
    source_file='', scope='UNDERGROUND_ONLY', excluded_scopes=[],
    records=[
        SourceValueRecord('SYN-PF-A','power_factor',0.95,'','Sentetik tasarım girdisi','SYNTHETIC_INPUT_A','HIGH','SOURCE_REPORTED',''),
        SourceValueRecord('SYN-PF-B','power_factor',0.92,'','Sentetik kontrol senaryosu','SYNTHETIC_INPUT_B','HIGH','SOURCE_REPORTED',''),
    ],
    conflicts=[
        SourceConflictRecord(
            'SYN-PF-CONFLICT','HIGH','power_factor','Sentetik güç faktörü doğrulama uyuşmazlığı',
            ['SYN-PF-A','SYN-PF-B'],'UNRESOLVED',
            'Test amacıyla bilinçli oluşturulmuştur; gerçek bir doküman çelişkisi değildir.',
        )
    ],
    missing_required_data=['Üretici onaylı konstrüksiyon çizimi'],
    notes='Yalnız kaynak çelişkisi iş akışını sınamak için oluşturulmuş sentetik kayıtlardır.',
)
(EX/'synthetic_20km_audit_case.ucd.json').write_text(json.dumps(audit.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')

applied=deepcopy(base)
applied.project_name='Sentetik 20 km Katalog Uygulama Örneği'
applied.project_code='DITUS-DEMO-20KM-APPLIED'
merge_builtin_catalogs(applied.cable_library)
merge_synthetic_catalogs(applied.cable_library)
apply_catalog_candidate_to_project(
    applied,'SYN-MFR-A-MV40K5-AL400-35','SYN-MFR-A-MV40K5-AL400-35::P1',1,
    [s.name for s in applied.route_sections],
)
applied.cable.validation_notes.append('Sentetik Üretici A adayı sentetik güzergâha yalnız iş akışı gösterimi için atanmıştır.')
applied=project_with_synchronized_installation_geometry(applied)
(EX/'synthetic_20km_applied.ucd.json').write_text(json.dumps(applied.to_dict(),ensure_ascii=False,indent=2),encoding='utf-8')

suite={
  'suite_id':'DITUS_SYNTHETIC_20KM_REGRESSION',
  'scope':'UNDERGROUND_ONLY',
  'description':'Tamamen sentetik 20 km yeraltı kablo hattı regresyonu.',
  'source_type':'GENERATED_SYNTHETIC_DATA',
  'cases':[
    {'case_id':'SYN-20KM','purpose':'20 km çift devre ana sentetik örnek','route_length_m':20000.0,'project_file':'synthetic_20km_line.ucd.json'},
    {'case_id':'SYN-20KM-AUDIT','purpose':'Sentetik kaynak denetimi iş akışı','route_length_m':20000.0,'project_file':'synthetic_20km_audit_case.ucd.json'},
    {'case_id':'SYN-20KM-APPLIED','purpose':'Sentetik katalog uygulama ve raporlama iş akışı','route_length_m':20000.0,'project_file':'synthetic_20km_applied.ucd.json'},
  ],
}
(EX/'synthetic_20km_regression_suite.json').write_text(json.dumps(suite,ensure_ascii=False,indent=2),encoding='utf-8')
print('generated', *(x.name for x in [EX/'synthetic_20km_line.ucd.json',EX/'synthetic_20km_audit_case.ucd.json',EX/'synthetic_20km_applied.ucd.json']))

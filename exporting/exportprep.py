# simplfies bone count using the merge weights function in CATS

import bpy
import traceback
import time
from .. import common as c
from ..interface.dictionary_en import t


def main(prep_type, simp_type, separate_hair, separate_head, remove_skirt, remove_breast):

    armature = bpy.data.objects['Armature']

    c.kklog('\nPrepping for export...')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    # Assume hidden items are unused and move them to their own collection
    c.kklog('Moving unused objects to their own collection...')
    no_move_objects = ['Bonelyfans', 'Shadowcast',
                       'Hitboxes', 'Body', 'Armature']
    for object in bpy.context.scene.objects:
        # print(object.name)
        move_this_one = object.name not in no_move_objects and 'Widget' not in object.name and object.hide
        if move_this_one:
            object.hide = False
            object.select_set(True)
            bpy.context.view_layer.objects.active = object
    if bpy.context.selected_objects:
        bpy.ops.object.move_to_collection(
            collection_index=0, is_new=True, new_collection_name='Unused clothing items')
    # hide the new collection
    try:
        bpy.context.scene.view_layers[0].active_layer_collection = bpy.context.view_layer.layer_collection.children['Unused clothing items']
        bpy.context.scene.view_layers[0].active_layer_collection.exclude = True
    except:
        try:
            # maybe the collection is in the default Collection collection
            bpy.context.scene.view_layers[0].active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection'].children['Unused clothing items']
            bpy.context.scene.view_layers[0].active_layer_collection.exclude = True
        except:
            # maybe the collection is already hidden, or doesn't exist
            pass

    c.kklog('Removing object outline modifier...')
    for ob in bpy.data.objects:
        if ob.modifiers.get('Outline Modifier'):
            ob.modifiers['Outline Modifier'].show_render = False
            ob.modifiers['Outline Modifier'].show_viewport = False
        # remove the outline materials because they won't be baked
        if ob in [obj for obj in bpy.context.view_layer.objects if obj.type == 'MESH']:
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            bpy.ops.object.material_slot_remove_unused()
    bpy.ops.object.select_all(action='DESELECT')
    body = bpy.data.objects['Body']
    bpy.context.view_layer.objects.active = body
    body.select_set(True)

    c.kklog('disabling uv warp modifiers on the eyes...')
    for ob in bpy.data.objects:
        if ob.modifiers.get('Left Eye UV warp'):
            ob.modifiers['Left Eye UV warp'].show_render = False
            ob.modifiers['Left Eye UV warp'].show_viewport = False
            ob.modifiers['Right Eye UV warp'].show_render = False
            ob.modifiers['Right Eye UV warp'].show_viewport = False

    # remove the second Template Eyewhite slot if there are two of the same name in a row
    index = 0
    for mat_slot_index in range(len(body.material_slots)):
        if body.material_slots[mat_slot_index].name == 'KK Eyewhites (sirome)':
            index = mat_slot_index
    if body.material_slots[index].name == body.material_slots[index-1].name:
        body.active_material_index = index
        bpy.ops.object.material_slot_remove()

    # Select the armature and make it active
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects['Armature'].hide_set(False)
    bpy.data.objects['Armature'].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects['Armature']
    bpy.ops.object.mode_set(mode='POSE')

    # If exporting for Unreal...
    if prep_type == 'E':
        armature = bpy.data.objects['Armature']
        bpy.context.view_layer.objects.active = armature

        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones['cf_j_waist02'].parent = armature.data.edit_bones['cf_j_hips']
        armature.data.edit_bones['cf_j_waist01'].parent = armature.data.edit_bones['cf_j_waist02']

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        armature.data.bones['cf_j_foot_L'].select = True
        armature.data.bones['cf_j_foot_R'].select = True
        armature.data.bones['cf_j_waist02'].select = True
        armature.data.bones['cf_s_waist02'].select = True
        #armature.data.bones['cf_j_waist01'].select = True
        #armature.data.bones['cf_s_waist01'].select = True
        #armature.data.bones['cf_j_spine01'].select = True
        #armature.data.bones['cf_s_spine01'].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

        armature.data.edit_bones['cf_s_leg_R'].parent = armature.data.edit_bones['cf_j_hips']
        armature.data.edit_bones['cf_s_leg_L'].parent = armature.data.edit_bones['cf_j_hips']

        ue_rename_dict = {
            'cf_j_hips': 'pelvis',
            #'cf_j_waist02': 'spine_01',
            'cf_j_waist01': 'spine_01',
            'cf_j_spine01': 'spine_02',
            'cf_j_spine02': 'spine_03',
            'cf_j_spine03': 'spine_04',
            'cf_j_neck': 'neck',
            'cf_j_head': 'head',
            'cf_j_shoulder_L': 'clavicle_l',
            'cf_j_shoulder_R': 'clavicle_r',
            'cf_j_arm00_L': 'upperarm_l',
            'cf_j_arm00_R': 'upperarm_r',
            'cf_j_forearm01_L': 'lowerarm_l',
            'cf_j_forearm01_R': 'lowerarm_r',
            'cf_j_hand_L': 'hand_l',
            'cf_j_hand_R': 'hand_r',
            'cf_J_hitomi_tx_L': 'eye_l',
            'cf_J_hitomi_tx_R': 'eye_r',

            'cf_j_thigh00_L': 'thigh_l',
            'cf_j_thigh00_R': 'thigh_r',
            'cf_j_leg01_L': 'calf_l',
            'cf_j_leg01_R': 'calf_r',
            'cf_j_leg03_L': 'foot_l',
            'cf_j_leg03_R': 'foot_r',
            'cf_j_toes_L': 'ball_l',
            'cf_j_toes_R': 'ball_r',

            'cf_j_index01_L': 'index_01_l',
            'cf_j_index02_L': 'index_02_l',
            'cf_j_index03_L': 'index_03_l',
            'cf_j_little01_L': 'pinky_01_l',
            'cf_j_little02_L': 'pinky_02_l',
            'cf_j_little03_L': 'pinky_03_l',
            'cf_j_middle01_L': 'middle_01_l',
            'cf_j_middle02_L': 'middle_02_l',
            'cf_j_middle03_L': 'middle_03_l',
            'cf_j_ring01_L': 'ring_01_l',
            'cf_j_ring02_L': 'ring_02_l',
            'cf_j_ring03_L': 'ring_03_l',
            'cf_j_thumb01_L': 'thumb_01_l',
            'cf_j_thumb02_L': 'thumb_02_l',
            'cf_j_thumb03_L': 'thumb_03_l',

            'cf_j_index01_R': 'index_01_r',
            'cf_j_index02_R': 'index_02_r',
            'cf_j_index03_R': 'index_03_r',
            'cf_j_little01_R': 'pinky_01_r',
            'cf_j_little02_R': 'pinky_02_r',
            'cf_j_little03_R': 'pinky_03_r',
            'cf_j_middle01_R': 'middle_01_r',
            'cf_j_middle02_R': 'middle_02_r',
            'cf_j_middle03_R': 'middle_03_r',
            'cf_j_ring01_R': 'ring_01_r',
            'cf_j_ring02_R': 'ring_02_r',
            'cf_j_ring03_R': 'ring_03_r',
            'cf_j_thumb01_R': 'thumb_01_r',
            'cf_j_thumb02_R': 'thumb_02_r',
            'cf_j_thumb03_R': 'thumb_03_r'
        }
        for bone in ue_rename_dict:
            if armature.data.bones.get(bone):
                armature.data.bones[bone].name = ue_rename_dict[bone]
        armature.data.bones['cf_d_sk_top'].name = 'skirt'
        armature.data.bones['cf_d_bust00'].name = 'breasts'

        armature.data.edit_bones['spine_01'].parent = armature.data.edit_bones['pelvis']
        armature.data.edit_bones['spine_02'].parent = armature.data.edit_bones['spine_01']
        armature.data.edit_bones['spine_03'].parent = armature.data.edit_bones['spine_02']
        armature.data.edit_bones['thigh_l'].parent = armature.data.edit_bones['pelvis']
        armature.data.edit_bones['thigh_r'].parent = armature.data.edit_bones['pelvis']
        armature.data.edit_bones['pelvis'].parent = None
        armature.data.edit_bones.remove(armature.data.edit_bones['BodyTop'])

        '''private_parts = armature.data.edit_bones.new("private")
        private_parts.head = (0,0,0.8)
        private_parts.tail = (0,0,0.81)
        private_parts.parent = armature.data.edit_bones['pelvis']
        for private_part in ['cf_d_siri_L','cf_d_ana','cf_d_kokan','cf_d_siri_R','cf_d_sirihit_L','cf_d_sirihit_R']:
            armature.data.edit_bones[private_part].parent = private_parts'''

        ue_ik_bones = {
            'ik_foot_l': 'foot_l',
            'ik_foot_r': 'foot_r',
            'ik_hand_gun': 'hand_r',
            'ik_hand_l': 'hand_l',
            'ik_hand_r': 'hand_r'
        }

        ik_foot_root=armature.data.edit_bones.new('ik_foot_root')
        ik_foot_root.head = (0,0,0.013)
        ik_foot_root.tail = (0,0,0.023)
        ik_hand_root=armature.data.edit_bones.new('ik_hand_root')
        ik_hand_root.head = (0,0,0.013)
        ik_hand_root.tail = (0,0,0.023)
        for bone in ue_ik_bones:
            new_bone=armature.data.edit_bones.new(bone)
            new_bone.head = armature.data.edit_bones[ue_ik_bones[bone]].head
            new_bone.tail = armature.data.edit_bones[ue_ik_bones[bone]].tail

        armature.data.edit_bones['ik_foot_l'].parent = armature.data.edit_bones['ik_foot_root']
        armature.data.edit_bones['ik_foot_r'].parent = armature.data.edit_bones['ik_foot_root']
        armature.data.edit_bones['ik_hand_gun'].parent = armature.data.edit_bones['ik_hand_root']
        armature.data.edit_bones['ik_hand_l'].parent = armature.data.edit_bones['ik_hand_gun']
        armature.data.edit_bones['ik_hand_r'].parent = armature.data.edit_bones['ik_hand_gun']

        replace_dict = {
            '_L': '_l',
            '_R': '_r',

            '_shoulder': '_clavicle',
            '_arm': '_upperarm',
            '_forearm': '_lowerarm',

            '_leg': '_calf',

            '_waist01': '_spine_01',
            '_spine01': '_spine_02',
            '_spine02': '_spine_03',
            '_spine03': '_spine_04',

            '_sk_': '_skirt_',

            'shoulder02': 'clavicle',

            'ct_hairB': 'hair_back',
            'ct_hairF': 'hair_front',
            'ct_hairS': 'hair_side'
        }

        for keyword in replace_dict:
            for bone in armature.data.bones:
                if keyword in bone.name:
                    bone.name = bone.name.replace(keyword, replace_dict[keyword])
        
        for bone in armature.data.edit_bones:
            if 'cf_s' in bone.name.lower():
                bone.name = 'deform' + str(bone.name)[4:]

        for bone in armature.data.edit_bones:
            if 'cf_j' in bone.name.lower():
                bone.name = 'joint' + str(bone.name)[4:]

        pelvis=armature.data.edit_bones['pelvis']
        pelvis.head = (0,0,0.883546)
        pelvis.tail = (0,0,0.96688)

        '''root=armature.data.edit_bones.new('root')
        root.head = (0,0,0.013)
        root.tail = (0,0,0.023)
        for child in ['pelvis','ik_foot_root','ik_hand_root']:
            armature.data.edit_bones[child].parent = root'''

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        if remove_skirt:
            for bone in armature.data.bones['skirt'].children_recursive:
                bone.select = True
            armature.data.bones['skirt'].select = True

        if remove_breast:
            for bone in armature.data.bones['breasts'].children_recursive:
                bone.select = True
            armature.data.bones['breasts'].select = True

        for bone in armature.data.bones:
            for keyword_merge in ['cf_d', 'vagina', 'k_f_', 'cf_hit_', 'backsk', 'siri', 'kokan', '_ana', 'cm_j_dan', '_pee', 'deform_hand']:
                if keyword_merge in bone.name.lower():
                    bone.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

        for parts_remove in ['cf_n_height', 'p_cf_body_bone', 'p_cf_body_00', 'HeadRef', 'joint_spinesk_00', 'ct_head']:
            for bone in armature.data.edit_bones[parts_remove].children_recursive:
                armature.data.edit_bones.remove(bone)
            armature.data.edit_bones.remove(
                armature.data.edit_bones[parts_remove])

        for bone in armature.data.edit_bones:
            for keyword_delete in ['cf_d', 'vagina', 'k_f_', 'cf_hit_', 'ct_', 'backsk', 'a_n', 'ollider', 'n_cam_', 'aim', 'siri', 'kokan', '_ana', 'cm_j_dan', '_pee', 'deform_hand']:
                if keyword_delete in bone.name.lower():
                    armature.data.edit_bones.remove(bone)
                    break

        # if separate the hair...
        if separate_hair:
            show_bones()

            armature = bpy.data.objects['Armature']
            # Select bones on layer 10
            for hair_part in ['hair_back', 'hair_front', 'hair_side']:
                for bone in armature.data.bones[hair_part].children_recursive:
                    bone.select = True
                armature.data.bones[hair_part].select = True

            # Separate the hair bones to a new armature
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.separate()
            new_armature = bpy.data.objects['Armature.001']
            new_armature.name = "HairArmature"
            bpy.context.view_layer.objects.active = new_armature
            bpy.ops.object.mode_set(mode='EDIT')

            '''root=new_armature.data.edit_bones.new('root')
            root.head = (0,0,0.013)
            root.tail = (0,0,0.023)
            for child in ['hair_back','hair_front','hair_side']:
                new_armature.data.edit_bones[child].parent = root'''
            #root_bone = new_armature.data.edit_bones.new('root')
            #new_armature.data.edit_bones['hair_back'].parent = root_bone
            #new_armature.data.edit_bones['hair_front'].parent = root_bone

            # Move hair meshes to the new armature
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
            bpy.data.objects['Hair Outfit 00'].select_set(True)
            bpy.context.view_layer.objects.active = new_armature
            bpy.ops.object.parent_set(type='ARMATURE')
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')

        if separate_head:
            show_bones()

            armature = bpy.data.objects['Armature']
            bpy.context.view_layer.objects.active = armature
            #armature.data.bones['cf_s_head'].select = True
            for bone in armature.data.bones['deform_head'].children_recursive:
                bone.select = True

            # Separate the head bones to a new armature
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.armature.separate()
            new_armature = bpy.data.objects['Armature.001']
            new_armature.name = "HeadArmature"
            bpy.context.view_layer.objects.active = new_armature
            bpy.ops.object.mode_set(mode='EDIT')

            '''root=new_armature.data.edit_bones.new('root')
            root.head = (0,0,0.013)
            root.tail = (0,0,0.023)
            for child in ['joint_tang_01','N_EyesLookTargetP','p_cf_head_bone']:
                new_armature.data.edit_bones[child].parent = root'''

            bpy.context.view_layer.objects.active = bpy.data.objects['Body']
            bpy.data.objects['Body'].select = True
            bpy.ops.mesh.separate(type='MATERIAL')
            bpy.data.objects['Body'].select = False
            head = bpy.data.objects['Body.002']
            bpy.context.view_layer.objects.active = head
            bpy.ops.object.join()
            head.name = "Head"

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = new_armature
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action="DESELECT")
            head.select = True
            bpy.context.view_layer.objects.active = new_armature
            bpy.ops.object.parent_set(type='ARMATURE')


    # If simplifying the bones...
    if simp_type in ['A', 'B']:
        show_bones()

        # Move pupil bones to layer 1
        armature = bpy.data.objects['Armature']
        if armature.data.bones.get('Left Eye'):
            armature.data.bones['Left Eye'].layers[0] = True
            armature.data.bones['Left Eye'].layers[10] = False
            armature.data.bones['Right Eye'].layers[0] = True
            armature.data.bones['Right Eye'].layers[10] = False

        # Select bones on layer 11
        for bone in armature.data.bones:
            if bone.layers[10] == True:
                bone.select = True

        # if very simple selected, also get 3-5,12,17-19
        if simp_type in ['A']:
            for bone in armature.data.bones:
                select_bool = bone.layers[2] or bone.layers[3] or bone.layers[4] or bone.layers[
                    11] or bone.layers[12] or bone.layers[16] or bone.layers[17] or bone.layers[18]
                if select_bool:
                    bone.select = True

        c.kklog('Using the merge weights function in CATS to simplify bones...')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

    # If exporting for VRM or VRC...
    if prep_type in ['A', 'D']:
        c.kklog('Editing armature for VRM...')
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')

        # Rearrange bones to match CATS output
        armature.data.edit_bones['Pelvis'].parent = None
        armature.data.edit_bones['Spine'].parent = armature.data.edit_bones['Pelvis']
        armature.data.edit_bones['Hips'].name = 'dont need lol'
        armature.data.edit_bones['Pelvis'].name = 'Hips'
        armature.data.edit_bones['Left leg'].parent = armature.data.edit_bones['Hips']
        armature.data.edit_bones['Right leg'].parent = armature.data.edit_bones['Hips']
        armature.data.edit_bones['Left ankle'].parent = armature.data.edit_bones['Left knee']
        armature.data.edit_bones['Right ankle'].parent = armature.data.edit_bones['Right knee']
        armature.data.edit_bones['Left shoulder'].parent = armature.data.edit_bones['Upper Chest']
        armature.data.edit_bones['Right shoulder'].parent = armature.data.edit_bones['Upper Chest']
        armature.data.edit_bones.remove(
            armature.data.edit_bones['dont need lol'])

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        # Merge specific bones for unity rig autodetect
        armature = bpy.data.objects['Armature']
        merge_these = ['cf_j_waist02', 'cf_s_waist01',
                       'cf_s_hand_L', 'cf_s_hand_R']
        # Delete the upper chest for VR chat models, since it apparently causes errors with eye tracking
        if prep_type == 'D':
            merge_these.append('Upper Chest')
        for bone in armature.data.bones:
            if bone.name in merge_these:
                bone.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

    # If exporting for MMD...
    if prep_type == 'C':
        # Create the empty
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.empty_add(
            type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
        empty = bpy.data.objects['Empty']
        bpy.ops.object.select_all(action='DESELECT')
        armature.parent = empty
        bpy.context.view_layer.objects.active = armature

        # rename bones to stock
        if armature.data.bones.get('Center'):
            bpy.ops.kkbp.switcharmature('INVOKE_DEFAULT')

        # then rename bones to japanese
        pmx_rename_dict = {
            '全ての親': 'cf_n_height',
            'センター': 'cf_j_hips',
            '上半身': 'cf_j_spine01',
            '上半身２': 'cf_j_spine02',
            '上半身３': 'cf_j_spine03',
            '首': 'cf_j_neck',
            '頭': 'cf_j_head',
            '両目': 'Eyesx',
            '左目': 'cf_J_hitomi_tx_L',
            '右目': 'cf_J_hitomi_tx_R',
            '左腕': 'cf_j_arm00_L',
            '右腕': 'cf_j_arm00_R',
            '左ひじ': 'cf_j_forearm01_L',
            '右ひじ': 'cf_j_forearm01_R',
            '左肩': 'cf_j_shoulder_L',
            '右肩': 'cf_j_shoulder_R',
            '左手首': 'cf_j_hand_L',
            '右手首': 'cf_j_hand_R',
            '左親指０': 'cf_j_thumb01_L',
            '左親指１': 'cf_j_thumb02_L',
            '左親指２': 'cf_j_thumb03_L',
            '左薬指１': 'cf_j_ring01_L',
            '左薬指２': 'cf_j_ring02_L',
            '左薬指３': 'cf_j_ring03_L',
            '左中指１': 'cf_j_middle01_L',
            '左中指２': 'cf_j_middle02_L',
            '左中指３': 'cf_j_middle03_L',
            '左小指１': 'cf_j_little01_L',
            '左小指２': 'cf_j_little02_L',
            '左小指３': 'cf_j_little03_L',
            '左人指１': 'cf_j_index01_L',
            '左人指２': 'cf_j_index02_L',
            '左人指３': 'cf_j_index03_L',
            '右親指０': 'cf_j_thumb01_R',
            '右親指１': 'cf_j_thumb02_R',
            '右親指２': 'cf_j_thumb03_R',
            '右薬指１': 'cf_j_ring01_R',
            '右薬指２': 'cf_j_ring02_R',
            '右薬指３': 'cf_j_ring03_R',
            '右中指１': 'cf_j_middle01_R',
            '右中指２': 'cf_j_middle02_R',
            '右中指３': 'cf_j_middle03_R',
            '右小指１': 'cf_j_little01_R',
            '右小指２': 'cf_j_little02_R',
            '右小指３': 'cf_j_little03_R',
            '右人指１': 'cf_j_index01_R',
            '右人指２': 'cf_j_index02_R',
            '右人指３': 'cf_j_index03_R',
            '下半身': 'cf_j_waist01',
            '左足': 'cf_j_thigh00_L',
            '右足': 'cf_j_thigh00_R',
            '左ひざ': 'cf_j_leg01_L',
            '右ひざ': 'cf_j_leg01_R',
            '左足首': 'cf_j_leg03_L',
            '右足首': 'cf_j_leg03_R',
        }

        for bone in pmx_rename_dict:
            armature.data.bones[pmx_rename_dict[bone]].name = bone

        # Rearrange bones to match a random pmx model I found
        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones['左肩'].parent = armature.data.edit_bones['上半身３']
        armature.data.edit_bones['右肩'].parent = armature.data.edit_bones['上半身３']
        armature.data.edit_bones['左足'].parent = armature.data.edit_bones['下半身']
        armature.data.edit_bones['右足'].parent = armature.data.edit_bones['下半身']

        # refresh the vertex groups? Bones will act as if they're detached if this isn't done
        body.vertex_groups.active = body.vertex_groups['BodyTop']

        # combine all objects into one

        # create leg IKs?

        c.kklog('Using CATS to simplify more bones for MMD...')

        # use mmd_tools to convert
        bpy.ops.mmd_tools.convert_to_mmd_model()

    bpy.ops.object.mode_set(mode='OBJECT')


def show_bones():
    # show all bones on the armature
    bpy.ops.object.mode_set(mode='POSE')
    allLayers = [True, True, True, True, True, True, True, True,
                 True, True, True, True, True, True, True, True,
                 True, True, True, True, True, True, True, True,
                 True, True, True, True, True, True, True, True]
    bpy.data.objects['Armature'].data.layers = allLayers
    bpy.ops.pose.select_all(action='DESELECT')


class export_prep(bpy.types.Operator):
    bl_idname = "kkbp.exportprep"
    bl_label = "Prep for target application"
    bl_description = t('export_prep_tt')
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = context.scene.kkbp
        prep_type = scene.prep_dropdown
        simp_type = scene.simp_dropdown
        separate_hair = scene.separate_hair_bool
        separate_head = scene.separate_head_bool
        remove_skirt = scene.remove_skirt_bool
        remove_breast = scene.remove_breast_bool
        last_step = time.time()
        try:
            c.toggle_console()
            main(prep_type, simp_type, separate_hair, separate_head, remove_skirt, remove_skirt)
            scene.plugin_state = 'prepped'
            c.kklog('Finished in ' + str(time.time() - last_step)[0:4] + 's')
            c.toggle_console()
            return {'FINISHED'}
        except:
            c.kklog('Unknown python error occurred', type='error')
            c.kklog(traceback.format_exc())
            self.report({'ERROR'}, traceback.format_exc())
            return {"CANCELLED"}


if __name__ == "__main__":
    bpy.utils.register_class(export_prep)

    # test call
    print((bpy.ops.kkbp.exportprep('INVOKE_DEFAULT')))

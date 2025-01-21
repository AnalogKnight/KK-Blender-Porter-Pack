#simplfies bone count using the merge weights function in CATS

import bpy, traceback, time, math
from .. import common as c
from ..interface.dictionary_en import t

def main(prep_type, simp_type, separate_hair, separate_head, remove_skirt, remove_breast):
    try:
        #always try to use the atlased model first
        body = bpy.data.objects['Body.001']
        bpy.context.view_layer.objects.active=body
        body_name = body.name
        armature_name = 'Armature.001'
        if not bpy.data.objects[armature_name].data.bones.get('Pelvis'):
            #the atlased body has already been modified. Skip.
            c.kklog('Model with atlas has already been prepped. Skipping export prep functions...', type='warn')
            return False
    except:
        #fallback to the non-atlased model if the atlased model collection is not visible
        body = bpy.data.objects['Body']
        bpy.context.view_layer.objects.active=body
        body_name = body.name
        armature_name = 'Armature'

    armature = bpy.data.objects[armature_name]

    c.kklog('\nPrepping for export...')
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    #Assume hidden items are unused and move them to their own collection
    c.kklog('Moving unused objects to their own collection...')
    no_move_objects = ['Bonelyfans', 'Shadowcast', 'Hitboxes', body_name, armature_name]
    for object in bpy.context.scene.objects:
        try:
            #print(object.name)
            move_this_one = object.name not in no_move_objects and 'Widget' not in object.name and object.hide_get()
            if move_this_one:
                object.hide_set(False)
                object.select_set(True)
                bpy.context.view_layer.objects.active=object
        except:
            c.kklog("During export prep, couldn't move object '{}' for some reason...".format(object), type='error')
    if bpy.context.selected_objects:
        bpy.ops.object.move_to_collection(collection_index=0, is_new=True, new_collection_name='Unused clothing items')
    #hide the new collection
    try:
        bpy.context.scene.view_layers[0].active_layer_collection = bpy.context.view_layer.layer_collection.children['Unused clothing items']
        bpy.context.scene.view_layers[0].active_layer_collection.exclude = True
    except:
        try:
            #maybe the collection is in the default Collection collection
            bpy.context.scene.view_layers[0].active_layer_collection = bpy.context.view_layer.layer_collection.children['Collection'].children['Unused clothing items']
            bpy.context.scene.view_layers[0].active_layer_collection.exclude = True
        except:
            #maybe the collection is already hidden, or doesn't exist
            pass
    
    c.kklog('Removing object outline modifier...')
    for ob in bpy.data.objects:
        if ob.modifiers.get('Outline Modifier'):
            ob.modifiers['Outline Modifier'].show_render = False
            ob.modifiers['Outline Modifier'].show_viewport = False
        #remove the outline materials because they won't be baked
        if ob in [obj for obj in bpy.context.view_layer.objects if obj.type == 'MESH']:
            ob.select_set(True)
            bpy.context.view_layer.objects.active=ob
            bpy.ops.object.material_slot_remove_unused()
    bpy.ops.object.select_all(action='DESELECT')
    body = bpy.data.objects[body_name]
    bpy.context.view_layer.objects.active=body
    body.select_set(True)

    c.kklog('disabling uv warp modifiers on the eyes...')
    for ob in bpy.data.objects:
        if ob.modifiers.get('Left Eye UV warp'):
            ob.modifiers['Left Eye UV warp'].show_render = False
            ob.modifiers['Left Eye UV warp'].show_viewport = False
            ob.modifiers['Right Eye UV warp'].show_render = False
            ob.modifiers['Right Eye UV warp'].show_viewport = False

    #Select the armature and make it active
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.data.objects[armature_name].hide_set(False)
    bpy.data.objects[armature_name].select_set(True)
    bpy.context.view_layer.objects.active=bpy.data.objects[armature_name]
    bpy.ops.object.mode_set(mode='POSE')

    # If exporting for Unreal...
    if prep_type == 'E':
        armature = bpy.data.objects['Armature']
        bpy.context.view_layer.objects.active = armature
        bpy.ops.armature.collection_show_all()

        bpy.ops.object.mode_set(mode='EDIT')

        #Clear IK, it won't work in unreal
        for bone in armature.pose.bones:
            for constraint in bone.constraints:
                bone.constraints.remove(constraint)

        armature.data.edit_bones['cf_j_waist02'].parent = armature.data.edit_bones['Hips']
        armature.data.edit_bones['Pelvis'].parent = armature.data.edit_bones['cf_j_waist02']

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        armature.data.bones['Left ankle'].select = True
        armature.data.bones['Right ankle'].select = True
        armature.data.bones['cf_j_waist02'].select = True
        armature.data.bones['cf_s_waist02'].select = True
        armature.data.bones['Pelvis'].select = True
        armature.data.bones['cf_s_waist01'].select = True
        #armature.data.bones['cf_j_spine01'].select = True
        #armature.data.bones['cf_s_spine01'].select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

        armature.data.edit_bones['cf_s_leg_R'].parent = armature.data.edit_bones['Hips']
        armature.data.edit_bones['cf_s_leg_L'].parent = armature.data.edit_bones['Hips']

        #Rename some bones to make it match Mannequin skeleton
        #Not necessary, but allows Unreal automatically recognize and match bone names when retargeting
        ue_rename_dict = {
            'Hips': 'pelvis',
            'Spine': 'spine_01',
            'Chest': 'spine_02',
            'Upper Chest': 'spine_03',
            'Neck': 'neck',
            'Head': 'head',
            'Left shoulder': 'clavicle_l',
            'Right shoulder': 'clavicle_r',
            'Left arm': 'upperarm_l',
            'Right arm': 'upperarm_r',
            'Left elbow': 'lowerarm_l',
            'Right elbow': 'lowerarm_r',
            'Left wrist': 'hand_l',
            'Right wrist': 'hand_r',
            'cf_J_hitomi_tx_L': 'eye_l',
            'cf_J_hitomi_tx_R': 'eye_r',
            'cf_s_shoulder02_l': 'deform_clavicle_l',
            'cf_s_shoulder02_r': 'deform_clavicle_r',

            'cf_s_bust00_L': 'joint_breast00_l',
            'cf_s_bust00_R': 'joint_breast00_r',

            'Left leg': 'thigh_l',
            'Right leg': 'thigh_r',
            'Left knee': 'calf_l',
            'Right knee': 'calf_r',
            'cf_j_leg03_L': 'foot_l',
            'cf_j_leg03_R': 'foot_r',
            'Left toe': 'ball_l',
            'Right toe': 'ball_r',

            'IndexFinger1_L': 'index_01_l',
            'IndexFinger2_L': 'index_02_l',
            'IndexFinger3_L': 'index_03_l',
            'cf_j_index04_L': 'index_04_l',
            'LittleFinger1_L': 'pinky_01_l',
            'LittleFinger2_L': 'pinky_02_l',
            'LittleFinger3_L': 'pinky_03_l',
            'cf_j_little04_L': 'pinky_04_l',
            'MiddleFinger1_L': 'middle_01_l',
            'MiddleFinger2_L': 'middle_02_l',
            'MiddleFinger3_L': 'middle_03_l',
            'cf_j_middle04_L': 'middle_04_l',
            'RingFinger1_L': 'ring_01_l',
            'RingFinger2_L': 'ring_02_l',
            'RingFinger3_L': 'ring_03_l',
            'cf_j_ring04_L': 'ring_04_l',
            'Thumb0_L': 'thumb_01_l',
            'Thumb1_L': 'thumb_02_l',
            'Thumb2_L': 'thumb_03_l',
            'cf_j_thumb04_L': 'thumb_04_l',

            'IndexFinger1_R': 'index_01_r',
            'IndexFinger2_R': 'index_02_r',
            'IndexFinger3_R': 'index_03_r',
            'cf_j_index04_R': 'index_04_r',
            'LittleFinger1_R': 'pinky_01_r',
            'LittleFinger2_R': 'pinky_02_r',
            'LittleFinger3_R': 'pinky_03_r',
            'cf_j_little04_R': 'pinky_04_r',
            'MiddleFinger1_R': 'middle_01_r',
            'MiddleFinger2_R': 'middle_02_r',
            'MiddleFinger3_R': 'middle_03_r',
            'cf_j_middle04_R': 'middle_04_r',
            'RingFinger1_R': 'ring_01_r',
            'RingFinger2_R': 'ring_02_r',
            'RingFinger3_R': 'ring_03_r',
            'cf_j_ring04_R': 'ring_04_r',
            'Thumb0_R': 'thumb_01_r',
            'Thumb1_R': 'thumb_02_r',
            'Thumb2_R': 'thumb_03_r',
            'cf_j_thumb04_R': 'thumb_04_r'
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
        #armature.data.edit_bones.remove(armature.data.edit_bones['Center'])

        '''private_parts = armature.data.edit_bones.new("private")
        private_parts.head = (0,0,0.8)
        private_parts.tail = (0,0,0.81)
        private_parts.parent = armature.data.edit_bones['pelvis']
        for private_part in ['cf_d_siri_L','cf_d_ana','cf_d_kokan','cf_d_siri_R','cf_d_sirihit_L','cf_d_sirihit_R']:
            armature.data.edit_bones[private_part].parent = private_parts'''

        #Create unreal ik bones,
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
            '_l': '_l',
            '_r': '_r',

            '_shoulder02': '_clavicle',
            '_shoulder': '_clavicle',
            '_arm': '_upperarm',
            '_forearm': '_lowerarm',

            '_leg': '_calf',

            '_waist01': '_spine_01',
            '_spine01': '_spine_02',
            '_spine02': '_spine_03',
            '_spine03': '_spine_04',

            '_bust': '_breast',
            '_bnip': '_nipple',

            '_sk_': '_skirt_',

            'ct_hairB': 'hair_back',
            'ct_hairF': 'hair_front',
            'ct_hairS': 'hair_side'
        }

        for keyword in replace_dict:
            for bone in armature.data.edit_bones:
                if keyword.lower() in bone.name.lower():
                    bone.name = bone.name.replace(keyword, replace_dict[keyword]).lower()
        
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
        
        for parts_remove in ['HeadRef', 'joint_spinesk_00', 'ct_head']:
            for bone in armature.data.edit_bones[parts_remove].children_recursive:
                armature.data.edit_bones.remove(bone)
            armature.data.edit_bones.remove(
                armature.data.edit_bones[parts_remove])

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
            for keyword_merge in ['cf_d',
                                  'vagina',
                                  'k_f_',
                                  'cf_hit_',
                                  'backsk',
                                  'siri',
                                  'kokan',
                                  '_ana',
                                  'cm_j_dan',
                                  '_pee',
                                  'deform_hand',
                                  'cf_d',
                                  'vagina',
                                  'k_f_',
                                  'cf_hit_',
                                  'ct_',
                                  'backsk',
                                  'a_n',
                                  'ollider',
                                  'n_cam_',
                                  'aim',
                                  'siri',
                                  'kokan',
                                  '_ana',
                                  'cm_j_dan',
                                  '_pee',
                                  'deform_hand',
                                  'Eye controller',
                                  'Center']:
                if keyword_merge in bone.name.lower():
                    bone.select = True
                    break

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

        '''for bone in armature.data.edit_bones:
            for keyword_delete in ['cf_d', 'vagina', 'k_f_', 'cf_hit_', 'ct_', 'backsk', 'a_n', 'ollider', 'n_cam_', 'aim', 'siri', 'kokan', '_ana', 'cm_j_dan', '_pee', 'deform_hand', 'Eye controller']:
                if keyword_delete in bone.name.lower():
                    armature.data.edit_bones.remove(bone)
                    break'''

        #Make all the bones on the legs face the same direction, otherwise IK won't work in Unreal
        armature.data.edit_bones["calf_l"].tail.z = armature.data.edit_bones["calf_l"].head.z + 0.1
        armature.data.edit_bones["calf_l"].head.y += 0.01
        armature.data.edit_bones["calf_r"].tail.z = armature.data.edit_bones["calf_r"].head.z + 0.1
        armature.data.edit_bones["calf_r"].head.y += 0.01

        armature.data.edit_bones["ball_l"].tail.z = armature.data.edit_bones["ball_l"].head.z
        armature.data.edit_bones["ball_l"].tail.y = armature.data.edit_bones["ball_l"].head.y - 0.05
        armature.data.edit_bones["ball_r"].tail.z = armature.data.edit_bones["ball_r"].head.z
        armature.data.edit_bones["ball_r"].tail.y = armature.data.edit_bones["ball_r"].head.y - 0.05

        #Same with arms
        for arm_bone in ['clavicle', 'upperarm', 'lowerarm', 'hand','deform_clavicle', 'deform_upperarm01','deform_upperarm02','deform_upperarm03','deform_lowerarm01','deform_lowerarm02','deform_wrist','deform_elbo','deform_elboback']:
            left = arm_bone + '_l'
            right = arm_bone + '_r'
            armature.data.edit_bones[left].tail.z = armature.data.edit_bones[left].head.z
            armature.data.edit_bones[left].tail.x = armature.data.edit_bones[left].head.x + 0.05
            armature.data.edit_bones[right].tail.z = armature.data.edit_bones[right].head.z
            armature.data.edit_bones[right].tail.x = armature.data.edit_bones[right].head.x - 0.05

        for finger_bone in ['index','pinky','middle','ring','thumb']:
            for i in range(1,4):
                left = finger_bone + '_0' + str(i) + '_l'
                left_next = finger_bone + '_0' + str(i+1) + '_l'
                right = finger_bone + '_0' + str(i) + '_r'
                right_next = finger_bone + '_0' + str(i+1) + '_r'
                armature.data.edit_bones[left].tail.z = armature.data.edit_bones[left_next].head.z
                armature.data.edit_bones[left].tail.x = armature.data.edit_bones[left_next].head.x
                armature.data.edit_bones[left].tail.y = armature.data.edit_bones[left_next].head.y

                armature.data.edit_bones[right].tail.z = armature.data.edit_bones[right_next].head.z
                armature.data.edit_bones[right].tail.x = armature.data.edit_bones[right_next].head.x
                armature.data.edit_bones[right].tail.y = armature.data.edit_bones[right_next].head.y

        if remove_breast == False:
            armature.data.edit_bones['breasts'].tail.z = armature.data.edit_bones['breasts'].head.z
            armature.data.edit_bones['breasts'].tail.y = armature.data.edit_bones['breasts'].head.y - 0.05
            for side in ['_l','_r']:
                breast_chain=['joint_breast00','joint_breast01','joint_breast02','joint_breast03','joint_nipple02root']
                for i in range(0,len(breast_chain)-1):
                    armature.data.edit_bones[breast_chain[i] + side].tail.x = armature.data.edit_bones[breast_chain[i + 1] + side].head.x
                    armature.data.edit_bones[breast_chain[i] + side].tail.y = armature.data.edit_bones[breast_chain[i + 1] + side].head.y
                    armature.data.edit_bones[breast_chain[i] + side].tail.z = armature.data.edit_bones[breast_chain[i + 1] + side].head.z

        root_bone = armature.data.edit_bones.new('root')
        root_bone.head = (0,0,0)
        root_bone.tail = (0.1,0,0)
        root_bone.roll = math.pi/2
        armature.data.edit_bones['pelvis'].parent = root_bone
        armature.data.edit_bones['ik_foot_root'].parent = root_bone
        armature.data.edit_bones['ik_hand_root'].parent = root_bone

        # if separate the hair...
        if separate_hair:
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.armature.collection_show_all()
            bpy.ops.pose.select_all(action='DESELECT')

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
            bpy.ops.object.mode_set(mode='POSE')
            bpy.ops.armature.collection_show_all()
            bpy.ops.pose.select_all(action='DESELECT')

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

        bpy.ops.object.mode_set(mode='POSE')

    #If simplifying the bones...
    if simp_type in ['A', 'B']:
        #show all bones on the armature
        bpy.ops.armature.collection_show_all()
        bpy.ops.pose.select_all(action='DESELECT')

        #Move pupil bones to layer 1
        armature = bpy.data.objects[armature_name]
        if armature.data.bones.get('Left Eye'):
            armature.data.bones['Left Eye'].collections.clear()
            armature.data.collections['0'].assign(armature.data.bones.get('Left Eye'))
            armature.data.bones['Right Eye'].collections.clear()
            armature.data.collections['0'].assign(armature.data.bones.get('Right Eye'))
        
        #Select bones on layer 11
        for bone in armature.data.bones:
            if bone.collections.get('10'):
                bone.select = True
        
        #if very simple selected, also get 3-5,12,17-19
        if simp_type in ['A']:
            for bone in armature.data.bones:
                select_bool = (bone.collections.get('2')  or 
                               bone.collections.get('3')  or 
                               bone.collections.get('4')  or 
                               bone.collections.get('11') or 
                               bone.collections.get('12') or 
                               bone.collections.get('16') or 
                               bone.collections.get('17') or 
                               bone.collections.get('18')
                               )
                if select_bool:
                    bone.select = True
        
        c.kklog('Using the merge weights function in CATS to simplify bones...')
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

    #If exporting for VRM or VRC...
    if prep_type in ['A', 'D']:
        c.kklog('Editing armature for VRM...')
        bpy.context.view_layer.objects.active=armature
        bpy.ops.object.mode_set(mode='EDIT')

        #Rearrange bones to match CATS output 
        if armature.data.edit_bones.get('Pelvis'):
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
            armature.data.edit_bones.remove(armature.data.edit_bones['dont need lol'])

        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.select_all(action='DESELECT')

        #Merge specific bones for unity rig autodetect
        armature = bpy.data.objects[armature_name]
        merge_these = ['cf_j_waist02', 'cf_s_waist01', 'cf_s_hand_L', 'cf_s_hand_R']
        #Delete the upper chest for VR chat models, since it apparently causes errors with eye tracking
        if prep_type == 'D':
            merge_these.append('Upper Chest')
        for bone in armature.data.bones:
            if bone.name in merge_these:
                bone.select = True

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.kkbp.cats_merge_weights()

    #If exporting for MMD...
    if prep_type == 'C':
        #Create the empty
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.empty_add(type='PLAIN_AXES', align='WORLD', location=(0, 0, 0))
        empty = bpy.data.objects['Empty']
        bpy.ops.object.select_all(action='DESELECT')
        armature.parent = empty
        bpy.context.view_layer.objects.active = armature

        #rename bones to stock
        if armature.data.bones.get('Center'):
            bpy.ops.kkbp.switcharmature('INVOKE_DEFAULT')
        
        #then rename bones to japanese
        pmx_rename_dict = {
        '全ての親':'cf_n_height',
        'センター':'cf_j_hips',
        '上半身':'cf_j_spine01',
        '上半身２':'cf_j_spine02',
        '上半身３':'cf_j_spine03',
        '首':'cf_j_neck',
        '頭':'cf_j_head',
        '両目':'Eyesx',
        '左目':'cf_J_hitomi_tx_L',
        '右目':'cf_J_hitomi_tx_R',
        '左腕':'cf_j_arm00_L',
        '右腕':'cf_j_arm00_R',
        '左ひじ':'cf_j_forearm01_L',
        '右ひじ':'cf_j_forearm01_R',
        '左肩':'cf_j_shoulder_L',
        '右肩':'cf_j_shoulder_R',
        '左手首':'cf_j_hand_L',
        '右手首':'cf_j_hand_R',
        '左親指０':'cf_j_thumb01_L',
        '左親指１':'cf_j_thumb02_L',
        '左親指２':'cf_j_thumb03_L',
        '左薬指１':'cf_j_ring01_L',
        '左薬指２':'cf_j_ring02_L',
        '左薬指３':'cf_j_ring03_L',
        '左中指１':'cf_j_middle01_L',
        '左中指２':'cf_j_middle02_L',
        '左中指３':'cf_j_middle03_L',
        '左小指１':'cf_j_little01_L',
        '左小指２':'cf_j_little02_L',
        '左小指３':'cf_j_little03_L',
        '左人指１':'cf_j_index01_L',
        '左人指２':'cf_j_index02_L',
        '左人指３':'cf_j_index03_L',
        '右親指０':'cf_j_thumb01_R',
        '右親指１':'cf_j_thumb02_R',
        '右親指２':'cf_j_thumb03_R',
        '右薬指１':'cf_j_ring01_R',
        '右薬指２':'cf_j_ring02_R',
        '右薬指３':'cf_j_ring03_R',
        '右中指１':'cf_j_middle01_R',
        '右中指２':'cf_j_middle02_R',
        '右中指３':'cf_j_middle03_R',
        '右小指１':'cf_j_little01_R',
        '右小指２':'cf_j_little02_R',
        '右小指３':'cf_j_little03_R',
        '右人指１':'cf_j_index01_R',
        '右人指２':'cf_j_index02_R',
        '右人指３':'cf_j_index03_R',
        '下半身':'cf_j_waist01',
        '左足':'cf_j_thigh00_L',
        '右足':'cf_j_thigh00_R',
        '左ひざ':'cf_j_leg01_L',
        '右ひざ':'cf_j_leg01_R',
        '左足首':'cf_j_leg03_L',
        '右足首':'cf_j_leg03_R',
        }

        for bone in pmx_rename_dict:
            armature.data.bones[pmx_rename_dict[bone]].name = bone
        
        #Rearrange bones to match a random pmx model I found 
        bpy.ops.object.mode_set(mode='EDIT')
        armature.data.edit_bones['左肩'].parent = armature.data.edit_bones['上半身３']
        armature.data.edit_bones['右肩'].parent = armature.data.edit_bones['上半身３']
        armature.data.edit_bones['左足'].parent = armature.data.edit_bones['下半身']
        armature.data.edit_bones['右足'].parent = armature.data.edit_bones['下半身']

        #refresh the vertex groups? Bones will act as if they're detached if this isn't done
        body.vertex_groups.active=body.vertex_groups['BodyTop']

        #combine all objects into one

        #create leg IKs?
        
        c.kklog('Using CATS to simplify more bones for MMD...')

        #use mmd_tools to convert
        bpy.ops.mmd_tools.convert_to_mmd_model()

    bpy.ops.object.mode_set(mode='OBJECT')

    #only disable the prep button if the non-atlas model has been modified.
    #This is because the model with atlas can be regenerated with the bake materials button
    return armature_name == 'Armature'

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
            if main(prep_type, simp_type, separate_hair, separate_head, remove_skirt, remove_breast):
                scene.plugin_state = 'prepped'
            c.kklog('Finished in ' + str(time.time() - last_step)[0:4] + 's')
            c.toggle_console()
            return {'FINISHED'}
        except:
            c.kklog('Unknown python error occurred', type = 'error')
            c.kklog(traceback.format_exc())
            self.report({'ERROR'}, traceback.format_exc())
            return {"CANCELLED"}
    

if __name__ == "__main__":
    bpy.utils.register_class(export_prep)

    # test call
    print((bpy.ops.kkbp.exportprep('INVOKE_DEFAULT')))

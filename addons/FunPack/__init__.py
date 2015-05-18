bl_info = {
	"name": "FunPack",
	"author": "Velem Novak",
	"version": (0, 1, 0),
	"blender": (2, 70, 0),
	"location": "Object > FunPack",
	"description": "UV packing game",
	"warning": "",
	"wiki_url": "http://www.blendercam.blogspot.com",
	"category": "Object"
}

import bpy
import math, random, os
def activate(ob):
	bpy.ops.object.select_all(action='DESELECT')
	ob.select=True
	bpy.context.scene.objects.active=ob



def createMeshFromData(name, verts, faces):
	# Create mesh and object
	me = bpy.data.meshes.new(name+'Mesh')
	ob = bpy.data.objects.new(name, me)
	#ob.show_name = True

	# Link object to scene and make active
	scn = bpy.context.scene
	scn.objects.link(ob)
	scn.objects.active = ob
	ob.select = True

	# Create mesh from given verts, faces.
	me.from_pydata(verts, [], faces)
	# Update mesh with new data
	me.update()	
	return ob


def GameDropOb(ob):
		
	activate(ob)
	#ob.rotation_euler.x=math.pi/2
	#bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
	#ob.location.z = ob.location.y
	#ob.location.x=0

	ob.select=True
	ob.game.physics_type='RIGID_BODY'
	ob.game.use_collision_bounds=True
	ob.game.collision_bounds_type = 'TRIANGLE_MESH'
	ob.game.collision_margin = 0.01
	ob.game.velocity_max = 1
	ob.game.damping = 0.5
	ob.game.rotation_damping = 0.9

	ob.game.lock_location_y = True
	ob.game.lock_rotation_x = True
	ob.game.lock_rotation_z = True


	bpy.ops.object.game_property_new(name="island")

		
def UVobs(obs):
	uvobs=[]
	zoffset=0
	for ob in obs:
		activate(ob)
		#ob = bpy.context.object
		bpy.ops.object.editmode_toggle()

		bpy.ops.uv.pack_islands(margin=0.01)
		bpy.ops.object.editmode_toggle()
		
		
		out_verts=[]
		out_faces=[]
		store_coords=[]
		for face in ob.data.polygons:
			oface=[]   
			for vert, loop in zip(face.vertices, face.loop_indices):
				coord = ob.data.vertices[vert].normal
				normal = ob.data.vertices[vert].co
				uv = ob.data.uv_layers.active.data[loop].uv 
				uv.y+=zoffset#we shift the uv to not collide when packing more objects
				out_verts.append((uv.x,0,uv.y))
				
				oface.append(loop)
			#print(oface)
			out_faces.append(oface)
		
		
		uvob = createMeshFromData(ob.name + 'UVObj', out_verts, out_faces)
		#print('d')
		activate(uvob)
		bpy.ops.mesh.uv_texture_add()

		for face in ob.data.polygons:
			oface=[]   
			for vert, loop in zip(face.vertices, face.loop_indices):
				
				uvob.data.uv_layers.active.data[loop].uv  = ob.data.uv_layers.active.data[loop].uv 
				
			
		
		bpy.ops.object.editmode_toggle()
		bpy.ops.mesh.remove_doubles()
		bpy.ops.object.editmode_toggle()
		bpy.ops.object.modifier_add(type='SOLIDIFY')
		bpy.context.object.modifiers["Solidify"].thickness = 0.1
		bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Solidify")
		uvob['source']=ob.name
		bpy.ops.object.editmode_toggle()
		bpy.ops.mesh.separate(type='LOOSE')
		bpy.ops.object.editmode_toggle()
		
		
		uvobs.extend(bpy.context.selected_objects)
		
		#for ob in bpy.context.selected_objects:
			#ob.location.z+=zoffset
			#print(zoffset)
		bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
		zoffset+=1
		
	for ob in uvobs:
		ob.select=True
		
	s=bpy.context.scene
	s.objects.active=uvobs[0]
	
	bpy.ops.object.material_slot_add()
	mat=bpy.data.materials.new('FunPackMaterial')
	
		
	uvobs[0].material_slots[0].material=mat
	mat.use_object_color = True
	for ob in uvobs:
		ob.color = (0.5+random.random(),0.5+random.random(),0.5+random.random(),1)
	mat.diffuse_color = (1,1,1)
	bpy.ops.object.make_links_data(type='MATERIAL')

	return uvobs

def doGame(context):
	
	#getIslands(bpy.context.active_object)
	obs=bpy.context.selected_objects
	origscene=bpy.context.scene
	import_scene('FunPack')
	
	
	
	
	uvobs = UVobs(obs)
			
	for ob in uvobs:
		GameDropOb(ob)
	
	bpy.ops.object.select_all(action='DESELECT')
	for ob in uvobs:
		ob.select=True
		
	bpy.ops.group.create()
	bpy.ops.object.make_links_scene(scene='FunPack')
	bpy.ops.object.delete(use_global=False)
	bpy.context.window.screen.scene = bpy.data.scenes['FunPack']
	
	bpy.ops.view3d.viewnumpad(type='CAMERA')
	bpy.context.space_data.viewport_shade = 'MATERIAL'
	#bpy.ops.view3d.zoom_camera_1_to_1()
	#bpy.context.scene.update()
	
	#PLAY THE GAME!
	bpy.ops.view3d.game_start()
	

	print('after game')
	#reassign UV's
	fdict={}
	bpy.context.scene.update()
	#get size object
	for ob in bpy.context.scene.objects:
		if ob.name[:5]=='ssize':
			scale=ob.location.z+1
	for uvob in uvobs:
		uvobmat=uvob.matrix_world
		
		for face1 in uvob.data.polygons:
			for vert1, loop1 in zip(face1.vertices, face1.loop_indices):
				uvtrans=uvob.data.uv_layers.active.data[loop1].uv
				
				co=uvobmat*uvob.data.vertices[vert1].co/scale
				fdict[uvtrans.x,uvtrans.y]=(co.x,co.z)
	#print(fdict)
	assigns=[]
	for ob in obs:
		for face in ob.data.polygons:
			for vert, loop in zip(face.vertices, face.loop_indices):
				uv=ob.data.uv_layers.active.data[loop].uv 	
				nuv = fdict[uv.x,uv.y]
				uv.x=nuv[0]
				uv.y=nuv[1]
				#assigns.append((uv,nuv))
	
	print(len(assigns))
		
	
	bpy.context.window.screen.scene = origscene
	bpy.data.scenes.remove(bpy.data.scenes['FunPack'])
	
#####################################################################
# Import Functions

def import_scene(obname):
	opath = "//data.blend\\Scene\\" + obname
	s = os.sep
	for p in bpy.utils.script_paths():
		fname= p + '%saddons%sFunPack%spack_scene.blend'
		dpath = p + \
			'%saddons%sFunPack%spack_scene.blend\\Scene\\' % (s, s, s)
		if os.path.isfile(fname):
			break
	# DEBUG
	#print('import_object: ' + opath)
	print(dpath,opath)
	result = bpy.ops.wm.append(
			filepath=opath,
			filename=obname,
			directory=dpath,
			filemode=1,
			link=False,
			autoselect=True,
			active_layer=True,
			instance_groups=True
		   )
	print(result)

	
import bpy


class FunPackUVOperator(bpy.types.Operator):
	"""Tooltip"""
	bl_idname = "object.fun_pack_uv"
	bl_label = "Fun Pack UV"

	@classmethod
	def poll(cls, context):
		return context.active_object is not None

	def execute(self, context):
		doGame(context)
		return {'FINISHED'}


def register():
	bpy.utils.register_class(FunPackUVOperator)


def unregister():
	bpy.utils.unregister_class(FunPackUVOperator)


if __name__ == "__main__":
	register()



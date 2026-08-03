"""The mesh, built in ONE place.

Stage 06 (production meshes) and stage 09 (the convergence study) must build
the mesh identically, or the study measures a different mesh from the one that
produces the results. They originally each had their own copy of the mesh
code, and that is precisely how the periodic-face defect below stayed
invisible: fixing it in one script would have left the other silently wrong,
and the convergence study would have "validated" a mesh nobody ran.
"""
import jpype

import config as C
import f3d_optics as O


def build(comp, sizes, textured=None, label=''):
    """Create mesh 'mesh1' on geom1 and run it. Returns (n_elem, min_quality).

    `sizes` is the per-material hmax dict from f3d_optics.mesh_sizes().
    """
    if textured is None:
        textured = C.TEXTURED

    meshes = comp.mesh()
    if 'mesh1' in [str(t) for t in meshes.tags()]:
        meshes.remove('mesh1')
    mesh = meshes.create('mesh1', 'geom1')

    # Global default = the coarsest material size; every domain then gets its
    # own Size feature, so this only covers anything unclaimed.
    sz = mesh.feature('size')          # auto-created with the mesh; fetch it
    sz.set('custom', 'on')
    sz.set('hmax', max(sizes.values()))
    sz.set('hmin', C.MESH['hmin'])

    for mat, selname in O.SELECTIONS.items():
        f = mesh.create(f'size_{mat}', 'Size')
        f.selection().geom('geom1', jpype.JInt(3))
        f.selection().named(selname)
        f.set('custom', 'on')
        f.set('hmax', sizes[mat])
        f.set('hmin', C.MESH['hmin'])

    # The cone additionally has to be resolved as a SHAPE, not just as a wave.
    # Skipped in the planar variant, where sel_cone is empty by construction.
    if textured:
        f = mesh.create('size_cone_geom', 'Size')
        f.selection().geom('geom1', jpype.JInt(3))
        f.selection().named('sel_cone')
        f.set('custom', 'on')
        f.set('hmax', min(C.MESH['hmax_tex'], sizes['fto']))
        f.set('hmin', C.MESH['hmin'])

    # ------------------------------------------- periodic face matching
    # A Floquet periodic condition ties each point on one face to its partner
    # on the opposite face. Free tets triangulate x=0 and x=pitch
    # independently, so those meshes do not match and the coupling has to be
    # interpolated -- an error that changes unpredictably with every remesh.
    #
    # Measured, before this was added: at 700 nm, meshes of 120153 / 120346 /
    # 123031 elements returned absorber absorptance 0.719 / 0.663 / 0.463. A
    # 36 % swing across a 2.5 % change in element count is not discretisation
    # error, and no amount of refinement would have converged it.
    #
    # So: mesh x=0 and y=0 explicitly, copy those meshes onto the opposite
    # faces, and only then fill the volume.
    # ORDER MATTERS, and getting it wrong is silent. Mesh features run in
    # sequence, and the x and y faces SHARE the cell's four vertical edges.
    # Meshing both x=0 and y=0 before copying either one means y=0 fixes its
    # own node distribution along the edge at x=pitch -- and the subsequent
    # copy of x=0 onto x=pitch then has to fit against that, so it cannot land
    # exactly. Measured with f3d_dbg_periodicity.py, that ordering gave
    # y-periodicity to 0.0002 % (median) but x-periodicity only to 0.2 %, with
    # 12 % outliers: the asymmetry is the tell, since with kFloquet = 0 both
    # directions must hold identically.
    #
    # Correct sequence: mesh x=0, copy it to x=pitch, and only THEN mesh y=0 --
    # whose edges at x=0 and x=pitch are by that point already fixed and
    # identical to each other -- and copy that to y=pitch.
    def free_tri(tag, selname):
        ft = mesh.create(tag, 'FreeTri')
        ft.selection().geom('geom1', jpype.JInt(2))
        ft.selection().named(selname)

    def copy_face(tag, src, dst):
        cp = mesh.create(tag, 'CopyFace')
        cp.selection('source').geom('geom1', jpype.JInt(2))
        cp.selection('source').named(src)
        cp.selection('destination').geom('geom1', jpype.JInt(2))
        cp.selection('destination').named(dst)

    free_tri('ftri_x0', 'sel_bnd_xmin')
    copy_face('cpf_x', 'sel_bnd_xmin', 'sel_bnd_xmax')
    free_tri('ftri_y0', 'sel_bnd_ymin')
    copy_face('cpf_y', 'sel_bnd_ymin', 'sel_bnd_ymax')

    mesh.create('ftet1', 'FreeTet')
    mesh.run()

    nelem = int(mesh.getNumElem())
    try:
        qmin = float(mesh.getMinQuality())
    except Exception:
        qmin = float('nan')
    if label:
        print(f'  {label}: {nelem} elements, min quality {qmin:.4f}')
    return nelem, qmin

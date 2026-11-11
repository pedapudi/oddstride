"""Refresh native family links and reject silently stale derived parameters."""
def refresh_native_family(design,source_document):
 assert source_document.dataFile.isComplete and not source_document.isModified
 source=fusion.Design.cast(source_document.products.itemByProductType('DesignProductType'))
 assert design.activateRootComponent()
 features=design.rootComponent.features.deriveFeatures
 assert features.count==1
 feature=features.item(0)
 assert len(feature.sourceEntities)==1
 assert feature.sourceEntities[0].objectType=='adsk::fusion::ConstructionPlane'
 assert feature.bodies.count==0
 if feature.documentReference.isOutOfDate:assert feature.documentReference.getLatestVersion()
 # On this Fusion build, a current reference can retain stale parameter values.
 # Reapplying the same native datum selection refreshes the actual dependency.
 assert feature.setSourceEntities(feature.sourceEntities,feature.excludedEntities)
 assert design.computeAll()
 rows=[]
 for parameter in design.derivedParameters:
  assert parameter.name.endswith('_Ref'),parameter.name
  source_name=parameter.name[:-4]
  source_parameter=source.userParameters.itemByName(source_name)
  assert source_parameter is not None,source_name
  error=abs(parameter.value-source_parameter.value)
  assert error<1e-9,(parameter.name,error)
  rows.append({'parameter':parameter.name,'source':source_name,'value':parameter.value,'unit':parameter.unit,'internal_unit_error':error})
 assert len(rows)==8
 assert feature.healthState==fusion.FeatureHealthStates.HealthyFeatureHealthState
 return {'source_version':source_document.dataFile.versionNumber,'parameters':rows,'geometry_bodies_added':0,'explicit_native_selection_refresh':True}

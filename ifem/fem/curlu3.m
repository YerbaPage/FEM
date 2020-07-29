function [curlu,volume,curlPhi] = curlu3(node,elem,u)
%% CURLU3 curl of an ND0 function in 3-D.
%
% curlu = curlu3(node,elem,u) compute the gradient of an ND0 vector field
% u on a 3-D mesh representing by edge basis lambda_i Dlambda_j - lambda_j Dlambda_i.
% 
% [curlu,volume,curlPhi] = curlu3(node,elem,u) also outputs volume and curlPhi
% which is the curl of ND0 basis. 
%
% curlu = curlu3(node,elem,u,Dlambda) compute the gradient with Dlambda. It
% will save time when Dlambda is available.
% 
% Local node index in a tetrahedron
%    _1_
%   / | \
%  2_ | _3
%    -4-
% 6 edges are indexed with incremental fashion.
% 
% See also gradu3, gradbasis3
%
% Added by Shuhao Cao, Apr 2020. 
%
% Copyright (C) Long Chen. See COPYRIGHT.txt for details.

%% Sort elem to ascend ordering
elem = sort(elem,2);
elem2edge = dof3edge(elem);
NT = size(elem,1);
[volume,elemSign] = simplexvolume(node,elem); 

%% Edge vector
locEdge = [1 2; 1 3; 1 4; 2 3; 2 4; 3 4];
elem2ve = zeros(NT,3,6);
for e = 1:6 % six edges
   elem2ve(:,:,e) = node(elem(:,locEdge(e,2)),:)-node(elem(:,locEdge(e,1)),:);
end

%% curlPhi is the scaled edge vector
curlPhi(:,:,6) = elem2ve(:,:,1);
curlPhi(:,:,1) = elem2ve(:,:,6);
curlPhi(:,:,2) = -elem2ve(:,:,5);
curlPhi(:,:,3) = elem2ve(:,:,4);
curlPhi(:,:,4) = elem2ve(:,:,3);
curlPhi(:,:,5) = -elem2ve(:,:,2);
curlPhi = curlPhi./repmat(volume.*elemSign,[1 3 6])/3;
% the above ordering is given for positive orientation and should be
% corrected by multiplying the elemSign

%% curl u is the composition of u and curlPhi
curlu = dot(permute(repmat(u(elem2edge),[1,1,3]),[1,3,2]),curlPhi,3);